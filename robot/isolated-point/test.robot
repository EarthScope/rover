
*** Settings ***
Suite Setup      Initialize Run Dir    ${RUN_DIR}

Library    Process
Library    OperatingSystem
Resource    ../common.robot

*** Variables ***
${RUN_DIR}    ${CURDIR}${/}run

*** Test Cases ***

Isolated Point

    Run Process    rover  --no-web  retrieve  TA_S22A__LHZ  2010-01-06T17:00:00  2010-01-06T18:00:00  cwd=${RUN_DIR}  stderr=retrieve-error-1.txt

    Normalize Error File    ${RUN_DIR}${/}retrieve-error-1.txt    100

    ${run} =    Get File    ${RUN_DIR}${/}retrieve-error-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-error-1.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  --no-web  retrieve  TA_S22A__LHZ  2010-01-06T17:00:00  2010-01-06T18:00:00  cwd=${RUN_DIR}  stderr=retrieve-error-2.txt

    Normalize Error File    ${RUN_DIR}${/}retrieve-error-2.txt    100

    ${run} =    Get File    ${RUN_DIR}${/}retrieve-error-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-error-2.txt
    Should Be Equal    ${run}  ${target}
