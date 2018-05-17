
*** Settings ***

Library    Process
Library    OperatingSystem

Test Setup    Set Environment Variable    PYTHONPATH  ../../../../rover


*** Test Cases ***

Compact

    Remove Directory    ${CURDIR}${/}run  resursive=True
    Create Directory    ${CURDIR}${/}run

    ${result} =  Run Process    python  -m  rover  -f  ../roverrc  ingest  ../../../tests/data/IU.ANMO.00.*-2010-02-27T04:30:00.000-2010-02-27T08:30:00.000.mseed  cwd=${CURDIR}${/}run
    Log    ${result.stderr}
    File Should Exist    ${CURDIR}${/}run${/}mseed${/}IU${/}2010${/}058${/}ANMO.IU.2010.058

    ${result} =  Run Process    python  -m  rover  -f  ../roverrc  compact  --all  --compact-list  cwd=${CURDIR}${/}run
    Log    ${result.stderr}
    Should Be Equal  ${result.stderr}  ${EMPTY}

    ${result} =  Run Process    python  -m  rover  -f  ../roverrc  ingest  ../../../tests/data/IU.ANMO.00.*-2010-02-27T04:30:00.000-2010-02-27T08:30:00.000.mseed  cwd=${CURDIR}${/}run
    Log    ${result.stderr}

    ${result} =  Run Process    python  -m  rover  -f  ../roverrc  compact  --all  --compact-list    cwd=${CURDIR}${/}run
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  duplicate data

    ${result} =  Run Process    python  -m  rover  -f  ../roverrc  compact  --all    cwd=${CURDIR}${/}run
    Log    ${result.stderr}
    Log    ${result.stdout}

    ${result} =  Run Process    python  -m  rover  -f  ../roverrc  compact  --all  --compact-list    cwd=${CURDIR}${/}run
    Log    ${result.stderr}
    Should Be Equal  ${result.stderr}  ${EMPTY}
