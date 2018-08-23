
*** Settings ***

Library    Process
Library    OperatingSystem


*** Test Cases ***

Bad Download URL

    Remove Directory    ${CURDIR}${/}run  resursive=True
    Create Directory    ${CURDIR}${/}run

    Run Process    rover  -f  ../rover.config  download  http://example.com/bad  cwd=${CURDIR}${/}run  stderr=download.txt
    Run Process    sed  -i  -e  's/[0-9\\-]\\+T[0-9:]\\+/DATE/g'  download.txt  cwd=${CURDIR}${/}run  shell=True
    ${run} =    Get File    ${CURDIR}${/}run${/}download.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}download.txt
    Should Be Equal    ${run}  ${target}

