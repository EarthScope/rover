
*** Settings ***
Suite Setup      Initialize Run Dir    ${RUN_DIR}

Library    Process
Library    OperatingSystem
Resource    ../common.robot

*** Variables ***
${RUN_DIR}    ${CURDIR}${/}run

*** Test Cases ***

Null Timespan

    Run Process    rover  --no-web  --dev  retrieve  ../retrieve  cwd=${RUN_DIR}  stderr=retrieve-error-1.txt

    Normalize Error File    ${RUN_DIR}${/}retrieve-error-1.txt    10

    ${run} =    Get File    ${RUN_DIR}${/}retrieve-error-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-error-1.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  --no-web  list-index  *_*_*_*  join-qsr  cwd=${RUN_DIR}  stdout=list-index.txt
    ${run} =    Get File    ${RUN_DIR}${/}list-index.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  --no-web  --dev  retrieve  ../retrieve  cwd=${RUN_DIR}  stderr=retrieve-error-2.txt

    Normalize Error File    ${RUN_DIR}${/}retrieve-error-2.txt    7

    ${run} =    Get File    ${RUN_DIR}${/}retrieve-error-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-error-2.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  --no-web  list-index  *_*_*_*  join-qsr  cwd=${RUN_DIR}  stdout=list-index.txt
    ${run} =    Get File    ${RUN_DIR}${/}list-index.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index.txt
    Should Be Equal    ${run}  ${target}
