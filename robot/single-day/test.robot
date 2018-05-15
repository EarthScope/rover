
*** Settings ***

Library    Process
Library    OperatingSystem

Test Setup    Set Environment Variable    PYTHONPATH  ../../../../rover

*** Test Cases ***

Single Day

    Remove Directory    ${CURDIR}${/}run  resursive=True
    Create Directory    ${CURDIR}${/}run
    ${result} =    Run Process    python  -c  print('goodbye world')
    LOG  ${result}
    LOG  ${result.stdout}
    LOG  ${result.stderr}
    ${result} =    Run Process    python  -m  rover  -f  ../roverrc  retrieve  IU.ANMO  2016-01-01  2016-01-02  cwd=${CURDIR}${/}run  stdout=${CURDIR}${/}run${/}console.log
    LOG  ${result}
    LOG  ${result.stdout}
    LOG  ${result.stderr}
