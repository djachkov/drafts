# coding: utf8
import datetime
import os
from pprint import pprint

from atlassian import Bamboo

GLOBAL_EXPIRY = dict(days=2, keep=2)


def get_expiry_settings():
    expiry_settings = {}
    expiry_data = bamboo.get_custom_expiry(limit=2000)
    do_not_expired = []
    for item in expiry_data["results"]:
        if not item["expiryConfig"]["expiryTypeNothing"]:
            expiry_settings[item["planKey"]] = dict(
                days=int(item["expiryConfig"]["duration"]),
                keep=int(item["expiryConfig"]["buildsToKeep"]),
            )
        else:
            do_not_expired.append(item["planKey"])
    return expiry_settings


def get_all_projects():
    return [project["key"] for project in bamboo.projects()]


def get_plans_from_project(project):
    return [plan["key"] for plan in bamboo.project_plans(project)]


def get_branches_from_plan(plan_key):
    return [branch["id"] for branch in bamboo.search_branches(plan_key)]


def get_results_from_branch(plan_key):
    return [
        results
        for results in bamboo.results(
            plan_key, include_all_states=True, expand="results.result"
        )
    ]


def get_plan_expiry(plan, settings):
    if plan in settings:
        days = settings[plan]["days"]
        keep = settings[plan]["keep"]
    else:
        days = GLOBAL_EXPIRY["days"]
        keep = GLOBAL_EXPIRY["keep"]
    return days, keep


def get_unknown(results):

    return [
        result["buildResultKey"]
        for result in results
        if result["buildState"] in ["Unknown", "Incomplete"]
    ]


def relative_time_to_actual(long_time_ago):
    mapping = {"year": 365, "month": 30, "week": 7, "day": 1, "hour": 0, "minute": 0}

    relative = long_time_ago.split()[:2]
    try:
        relative[1] = mapping[relative[1].strip("s")]
    except KeyError:
        relative[1] = 0
    except IndexError:
        print(relative)
        relative.append(0)
    actual = int(relative[0]) * int(relative[1])
    delta_actual = datetime.timedelta(days=int(actual))
    return delta_actual


def process_results(plan_results, keep=2, days=2):
    processed = {}
    current_date = datetime.date.today()
    time_delta = datetime.timedelta(days=int(days))
    check_date = current_date - time_delta
    keep_count = 1
    if len(plan_results) <= keep:
        return

    for result in plan_results:
        if keep_count <= keep:
            keep_count += 1
            continue
        if "buildCompletedTime" in result:
            t = result["buildCompletedTime"].split("T")[0]
            build_date = datetime.datetime.strptime(t, "%Y-%m-%d").date()
        elif "buildStartedTime" in result:
            t = result["buildStartedTime"].split("T")[0]
            build_date = datetime.datetime.strptime(t, "%Y-%m-%d").date()
        elif "buildRelativeTime" in result and result["buildRelativeTime"]:
            t = result["buildRelativeTime"]
            build_date = current_date - relative_time_to_actual(t)
        else:
            pprint(result)
            continue
        if build_date <= check_date:

            if not result["plan"]["key"] in processed:
                processed[result["plan"]["key"]] = dict(total=0, builds=[],)
                processed[result["plan"]["key"]]["builds"].append(
                    dict(build_id=result["id"], build=result["buildResultKey"])
                )
                processed[result["plan"]["key"]]["total"] += 1
                continue
            else:
                processed[result["plan"]["key"]]["builds"].append(
                    dict(build_id=result["id"], build=result["buildResultKey"])
                )
                processed[result["plan"]["key"]]["total"] += 1
    return processed


def write_results(results):
    day = datetime.date.today().strftime("%d_%m_%Y")
    with open("{}-inspection_results.txt".format(day), "a+") as f:
        for key in results:
            f.write(key + "\n")
    return


def delete_build_results(list):
    for item in list:
        try:
            bamboo.delete_build_result(item)
            print("{} successfully deleted".format(item))
        except Exception:
            print(Exception)
            continue


# def merge_list(merge): return [item for oldlist in merge for item in oldlist]


def inspect_bamboo(
    key=None, inspect_all=True, delete=False, map_dir=True, unknown_only=False
):
    expiry_settings = get_expiry_settings()
    all_results = []
    if key:
        inspect_all = False
        projects = [key]
    if inspect_all:
        projects = get_all_projects()
    for project in projects:
        print("Inspecting {} project".format(project))
        plans = get_plans_from_project(project)
        for plan in plans:
            expiry_days, expiry_keep = get_plan_expiry(plan, expiry_settings)
            print("Inspecting {} plan".format(plan))
            branches = get_branches_from_plan(plan)
            for branch in branches:
                if map_dir:
                    with open("mapping.txt", "a+") as f:
                        f.write(
                            "{branch}:{tag}\n".format(
                                branch=branch,
                                tag=bamboo.plan_directory_info(branch)["results"][0][
                                    "storageTag"
                                ],
                            )
                        )
                if unknown_only:
                    results = get_unknown(get_results_from_branch(branch))
                    write_results(results)
                else:
                    branch_results = process_results(
                        get_results_from_branch(branch),
                        days=expiry_days,
                        keep=expiry_keep,
                    )
                    if branch_results:
                        results = [
                            key["build"] for key in branch_results[branch]["builds"]
                        ]
                        write_results(results)
                if delete:
                    delete_build_results(all_results)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     '-k', '--key'
    # )
    # parser.add_argument(
    #     '-d', '--days'
    # )
    # parser.add_argument(
    #     '--map_dir', type=bool, nargs='?',
    #     const=True, default=False,
    # )
    # parser.add_argument(
    #     '-s', '--secret'
    # )
    # parser.add_argument(
    #     "--delete"
    # )
    # parser.add_argument(
    #     "--unknown"
    # )
    # args = parser.parse_args()

    BAMBOO_URL = os.environ.get("BAMBOO_URL",)
    ATLASSIAN_USER = os.environ.get("ATLASSIAN_USER",)
    ATLASSIAN_PASSWORD = os.environ.get("ATLASSIAN_PASSWORD",)

    bamboo = Bamboo(
        url=BAMBOO_URL, username=ATLASSIAN_USER, password=ATLASSIAN_PASSWORD
    )

    inspect_bamboo(key="DS", delete=False)
    # expiry_data = bamboo.get_custom_expiry(limit=20)
    # pprint(expiry_data)
