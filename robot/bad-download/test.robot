
*** Settings ***

Library    Process
Library    OperatingSystem


*** Test Cases ***

Bad Download URL

    Remove Directory    ${CURDIR}${/}run  recursive=True
    Create Directory    ${CURDIR}${/}run

    Run Process    rover  -f  ../rover.config  download  http://example.com/bad?foo\=bar&baz\=boo  cwd=${CURDIR}${/}run  stderr=download.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}download.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}download.txt
    Should Be Equal    ${run}  ${target}

