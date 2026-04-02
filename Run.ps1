# Устанавливаем кодировку UTF-8 для корректного вывода
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Путь к виртуальному окружению
$venvPath = ".venv"
# Путь к UPX (лежит в корне проекта)
$upxPath = ".\upx.exe"
# Имя выходной папки и файла
$outputDir = "Ares Foundation Generator Plus"
$exeName = "Ares Foundation Generator Plus.exe"
$exeFullPath = "$outputDir\$exeName"

# Режим сборки: "onefile" или "standalone"
$buildMode = "standalone"

# Временное включение консоли для отладки (замените на $true, чтобы увидеть ошибки)
$debugConsole = $false

# Проверка наличия виртуального окружения
if (-not (Test-Path "$venvPath\Scripts\python.exe")) {
    Write-Host "Ошибка: Не найден python.exe в $venvPath\Scripts."
    exit 1
}

# Определение разрядности Python из venv
$pythonInfo = & "$venvPath\Scripts\python.exe" -c "import platform; print(platform.architecture()[0])"
$is64bit = $pythonInfo -eq "64bit"
Write-Host "Используется Python: $pythonInfo ($(if($is64bit){'x64'}else{'x86'}))"

# Базовые аргументы Nuitka (общие для обоих режимов)
$nuitkaArgs = @(
    "--standalone",
    "--enable-plugin=tk-inter",
    "--include-data-dir=icons=icons",
    "--include-data-files=Unifont.ttf=./",
    "--include-data-files=icon.ico=./",
    "--include-data-files=icon.png=./",
    "--assume-yes-for-downloads",
    "--noinclude-dlls=*.test.dll",
    "--lto=yes",
    "--static-libpython=no",
    "--remove-output",
    "--output-dir=$outputDir",
    "--output-filename=$exeName",
    "--windows-icon-from-ico=icon.ico",
    "--company-name=YoWassup Inc",
    "--product-name=Ares Foundation Generator Plus",
    "--file-version=1.0.0.0",
    "--product-version=1.0.0.0",
    "--file-description=Ares Foundation Generator Plus",
    "--copyright=© 2026 YoWassup Inc. Все права защищены.",
    "main.py"
)

# Управление консолью
if ($debugConsole) {
    $nuitkaArgs += "--windows-console-mode=force"
} else {
    $nuitkaArgs += "--windows-console-mode=disable"
}

# Добавляем флаги в зависимости от режима
if ($buildMode -eq "onefile") {
    Write-Host "Режим сборки: однофайловый (--onefile)"
    $nuitkaArgs += "--onefile"
    $nuitkaArgs += "--onefile-no-compression"
} else {
    Write-Host "Режим сборки: папка (--standalone)"
    # В standalone режиме не добавляем --onefile
}

# Добавляем флаг компилятора в зависимости от разрядности
if ($is64bit) {
    Write-Host "Выбран компилятор: Zig"
    $nuitkaArgs += "--zig"
} else {
    Write-Host "Выбран компилятор: MinGW64"
    $nuitkaArgs += "--mingw64"
}

# Запуск компиляции
Write-Host "Запуск Nuitka..."
& "$venvPath\Scripts\python.exe" -m nuitka $nuitkaArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "Ошибка компиляции Nuitka (код $LASTEXITCODE)."
    exit $LASTEXITCODE
}

# Для standalone режима перемещаем содержимое подпапки main.dist на уровень выше
if ($buildMode -eq "standalone") {
    $distSubdir = "$outputDir\main.dist"
    if (Test-Path $distSubdir) {
        Write-Host "Перемещение содержимого $distSubdir в $outputDir ..."
        Move-Item -Path "$distSubdir\*" -Destination $outputDir -Force
        Remove-Item -Path $distSubdir -Force
    }
}

# Копируем языковые файлы и settings.ini в папку с exe
Write-Host "Копирование языковых файлов и настроек..."
Copy-Item -Path "language_*.ini" -Destination $outputDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path "settings.ini" -Destination $outputDir -Force -ErrorAction SilentlyContinue

# Сжатие UPX (применяется к самому exe)
if (Test-Path $exeFullPath) {
    if (Test-Path $upxPath) {
        Write-Host "Применяем UPX сжатие к $exeFullPath ..."
        $originalSize = (Get-Item $exeFullPath).Length
        & $upxPath --best --lzma $exeFullPath
        if ($LASTEXITCODE -eq 0) {
            $newSize = (Get-Item $exeFullPath).Length
            Write-Host "UPX завершён. Размер уменьшен с $($originalSize / 1MB) МБ до $($newSize / 1MB) МБ."
        } else {
            Write-Host "UPX завершился с ошибкой (код $LASTEXITCODE)."
        }
    } else {
        Write-Host "UPX не найден, пропускаем сжатие."
    }
} else {
    Write-Host "Не найден исполняемый файл $exeFullPath. UPX не выполнен."
}

Write-Host "Готово! Исполняемый файл и ресурсы находятся в папке '$outputDir'."