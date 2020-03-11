# coding: utf8
from atlassian import Bamboo
import os
from pprint import pprint


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


def get_unknown(results):

    return [
        result["buildResultKey"]
        for result in results
        if result["buildState"] in ["Unknown", "Incomplete"]
    ]


def get_latest(project):
    return [
        result["buildResultKey"]
        for result in bamboo.project_latest_results(project, include_all_states=True)
    ]


if __name__ == "__main__":

    BAMBOO_URL = os.environ.get("BAMBOO_URL", "")
    ATLASSIAN_USER = os.environ.get("ATLASSIAN_USER", "")
    ATLASSIAN_PASSWORD = os.environ.get("ATLASSIAN_PASSWORD", "")
    # AMS
    bamboo = Bamboo(
        url=BAMBOO_URL, username=ATLASSIAN_USER, password=ATLASSIAN_PASSWORD
    )
    x = bamboo.get_custom_expiry(limit=10000)
    pprint(x)
    # projects = get_all_projects()
    # # projects = ["RFP"]
    # plans = []
    # latest = []
    # for project in projects:
    #     plans.extend(get_plans_from_project(project))
    #     latest.extend(get_latest(project))
    # branches = []
    # for plan in plans:
    #     branches.extend(get_branches_from_plan(plan))
    # results = []
    # for branch in branches:
    #     results.extend(get_results_from_branch(branch))
    # for branch in branches:
    #     bamboo.latest_results

    # prepare_list = get_unknown(results)
    # unknown = list(set(prepare_list) - set(latest))
    # with open("unknown_keys.txt", "w+") as f:
    #     for key in unknown:
    #         f.write(key + "\n")
    # print(latest)
    # print(unknown)
    # print(prepare_list)
    # if not unknown:
    #     print("Nothing to delete!")
    # else:
    #     for build in unknown:
    #         print("Delete build result: {}".format(build))
    #         bamboo.delete_build_result(build)

