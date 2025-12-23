
*** Settings ***
Suite Setup      Initialize Run Dir    ${RUN_DIR}

Library    Process
Library    OperatingSystem
Resource    ../common.robot

*** Variables ***
${RUN_DIR}    ${CURDIR}${/}run

*** Test Cases ***

Help
    Comment  check that help starts and shows basic info
    ${result} =    Run Process    rover  cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stdout}  help
    Should Match Regexp    ${result.stdout}  rover.config
