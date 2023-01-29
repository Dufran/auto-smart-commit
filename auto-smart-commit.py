#!/usr/bin/env python3

import re
import sys
from subprocess import check_output
from typing import NoReturn, Optional


def run_command(command: str) -> str:
    try:
        stdout: str = check_output(command.split()).decode("utf-8").strip()
    except Exception:
        stdout = ""
    return stdout


def current_git_branch_name() -> str:
    return run_command("git symbolic-ref --short HEAD")


def extract_jira_issue_key(message: str) -> Optional[str]:
    project_key, issue_number = r"[A-Z]{2,}", r"[0-9]+"
    match = re.search(f"{project_key}-{issue_number}", message)
    if match:
        return match.group(0)
    return None


def main() -> NoReturn:
    # ? https://confluence.atlassian.com/fisheye/using-smart-commits-960155400.html
    # Exit if the branch name does not contain a Jira issue key.
    git_branch_name = current_git_branch_name()
    jira_issue_key = extract_jira_issue_key(git_branch_name)
    if not jira_issue_key:
        sys.exit(0)
    # * Read the commit message.
    commit_msg_filepath = sys.argv[1]
    with open(commit_msg_filepath, "r") as f:
        commit_msg = f.read()
    # Split the commit into a subject and body and apply some light formatting.
    commit_elements = commit_msg.split("\n", maxsplit=1)
    commit_subject = commit_elements[0].strip()
    commit_subject = f"{commit_subject[:1].upper()}{commit_subject[1:]}"
    commit_subject = re.sub(r"\.+$", "", commit_subject)
    commit_body = None if len(commit_elements) == 1 else commit_elements[1].strip()
    # * Build the new commit message:
    # * 1. If there is a body, turn it into a comment on the issue.
    if "#comment" not in commit_msg and commit_body:
        commit_body = f"{jira_issue_key} #comment {commit_subject}\n\n{commit_body}"
    # * 2. Make sure the subject starts with a Jira issue key.
    if not extract_jira_issue_key(commit_subject):
        commit_subject = f"{jira_issue_key} {commit_body}"
    #! Override commit message.
    commit_msg = f"{commit_subject}" if commit_body else commit_subject
    with open(commit_msg_filepath, "w") as f:
        f.write(commit_msg)
    sys.exit(0)


if __name__ == "__main__":
    main()
