
*** Settings ***
Suite Setup      Initialize Run Dir    ${RUN_DIR}

Library    Process
Library    OperatingSystem
Resource    ../common.robot

*** Variables ***
${RUN_DIR}    ${CURDIR}${/}run

*** Test Cases ***

Bad Download URL

    Run Process    rover  download  http://example.com/bad?foo\=bar&baz\=boo  cwd=${CURDIR}${/}run  stderr=download.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}download.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}download.txt
    Should Be Equal    ${run}  ${target}
