@echo off
title ODPS data transfer tools 
SETLOCAL ENABLEDELAYEDEXPANSION
set "BASE_DIR=%~dp0"
pushd "%BASE_DIR%"

set MAIN_CLASS=com.aliyun.odps.ship.DShip
set "LIB_DIR=%BASE_DIR%lib\"

set "CLASSPATH=."
for %%F in ("%LIB_DIR%*.jar") do (
set "CLASSPATH=!CLASSPATH!;%%F"
)

set "CLASSPATH=!CLASSPATH!;%CONF_DIR%"

rem set java env
popd
java -Xms256m -Xmx1024m  %MAIN_CLASS% %*

ENDLOCAL
