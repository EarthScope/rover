
*** Settings ***
Suite Setup      Initialize Run Dir    ${RUN_DIR}

Library    Process
Library    OperatingSystem
Resource    ../common.robot

*** Variables ***
${RUN_DIR}    ${CURDIR}${/}run

*** Test Cases ***

Bad Date Format Command Line

    Run Process    rover  --no-web  retrieve  TA_MSTX__BH?  2012-02-01  2012-02-41  cwd=${RUN_DIR}  stderr=retrieve-error-1.txt
    Normalize Error File    ${RUN_DIR}${/}retrieve-error-1.txt    13
    ${run} =    Get File    ${RUN_DIR}${/}retrieve-error-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-error-1.txt
    Should Be Equal    ${run}  ${target}

Bad Date Format File

    Run Process    rover   --no-web  retrieve  ../TA_MSTX_BH_Feb2012.req  cwd=${RUN_DIR}  stderr=retrieve-error-2.txt
    Normalize Error File    ${RUN_DIR}${/}retrieve-error-2.txt    11
    ${run} =    Get File    ${RUN_DIR}${/}retrieve-error-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-error-2.txt
    Should Be Equal    ${run}  ${target}
