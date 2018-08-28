
*** Settings ***

Library    Process
Library    OperatingSystem

Suite Setup   Setup Run Directory


*** Keywords ***

Setup Run Directory
    Remove Directory    ${CURDIR}${/}run  recursive=True,
    Create Directory    ${CURDIR}${/}run


*** Test Cases ***

Init
    Comment  check that initialisation creates expected dirs and files
    ${result} =    Run Process    rover  init-repository  cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Directory Should Exist    ${CURDIR}${/}run${/}data
    Directory Should Exist    ${CURDIR}${/}run${/}logs
    File Should Exist    ${CURDIR}${/}run${/}logs/init-repository.log
    File Should Exist    ${CURDIR}${/}run${/}rover.config
    File Should Exist    ${CURDIR}${/}run${/}data${/}timeseries.sqlite

