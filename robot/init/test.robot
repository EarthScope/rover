
*** Settings ***
Suite Setup      Initialize Run Dir    ${RUN_DIR}

Library    Process
Library    OperatingSystem
Resource    ../common.robot

*** Variables ***
${RUN_DIR}    ${CURDIR}${/}run

*** Test Cases ***

Init
    Comment  check that initialization creates expected dirs and files
    ${result} =    Run Process    rover  init-repository  cwd=${RUN_DIR}
    Log    ${result.stdout}
    Log    ${result.stderr}
    Directory Should Exist    ${RUN_DIR}${/}data
    Directory Should Exist    ${RUN_DIR}${/}logs
    File Should Exist    ${RUN_DIR}${/}logs/init-repository.log
    File Should Exist    ${RUN_DIR}${/}rover.config
    File Should Exist    ${RUN_DIR}${/}data${/}timeseries.sqlite

