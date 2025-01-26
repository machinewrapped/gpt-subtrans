@echo off
setlocal

REM General setup
call install.bat

call envsubtrans\Scripts\activate.bat

echo.
echo WARNING: Amazon Bedrock setup is not recommended for most users.
echo The setup is complex and requires AWS credentials, region configuration,
echo and enabling specific model access in the AWS Console.
echo Proceed only if you are familiar with AWS configuration.
echo.
pause

REM Install AWS SDK
echo Installing AWS SDK for Python (boto3)...
pip install -U boto3

REM Check for existing .env file
if not exist .env (
    REM Create .env file
    echo Creating .env file to hold environment variables
    echo PROVIDER=Bedrock > .env
) else (
    REM Remove existing PROVIDER and add PROVIDER=Bedrock
    type .env | findstr /v "^PROVIDER=" > temp.env
    echo PROVIDER=Bedrock >> temp.env
    move /y temp.env .env > nul
)

REM Prompt for AWS Access Key ID
findstr /m "AWS_ACCESS_KEY_ID" .env > nul
if not errorlevel 1 (
    echo Found AWS_ACCESS_KEY_ID in .env file
    goto skip_access_key
)

echo Please enter your AWS Access Key ID:
set /p access_key=AWS_ACCESS_KEY_ID:

if not "%access_key%"=="" (
    echo AWS_ACCESS_KEY_ID=%access_key% >> .env
    echo AWS Access Key ID saved to .env
) else (
    echo No AWS Access Key ID entered. Skipping configuration.
    goto skip_config
)

:skip_access_key

REM Prompt for AWS Secret Access Key
findstr /m "AWS_SECRET_ACCESS_KEY" .env > nul
if not errorlevel 1 (
    echo Found AWS_SECRET_ACCESS_KEY in .env file
    goto skip_access_key
)

echo Please enter your AWS Secret Access Key:
set /p secret_key=AWS_SECRET_ACCESS_KEY:

if not "%secret_key%"=="" (
    echo AWS_SECRET_ACCESS_KEY=%secret_key% >> .env
    echo AWS Secret Access Key saved to .env
) else (
    echo No AWS Secret Access Key entered. Skipping configuration.
    goto skip_config
)

REM Prompt for AWS Region
findstr /m "AWS_REGION" .env > nul
if not errorlevel 1 (
    echo Found AWS_REGION in .env file
    goto skip_config
)

echo Please enter your AWS Region (e.g., us-east-1):
set /p aws_region=AWS_REGION:

if not "%aws_region%"=="" (
    echo AWS_REGION=%aws_region% >> .env
    echo AWS Region saved to .env
) else (
    echo No AWS Region entered.
)

:skip_config

REM Generate the Bedrock command
call scripts\generate-cmd.bat bedrock-subtrans

echo Default provider set to Bedrock
echo.
echo Installation complete. To uninstall, simply delete the directory.
exit /b 0
