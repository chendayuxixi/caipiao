@echo off
chcp 65001 >nul 2>nul
title Stock Fund Flow Animator
echo ========================================
echo   Stock Fund Flow Animator
echo ========================================
echo.

echo [1/2] Generating test animations (mock data)...
py test_animation.py
echo.

echo [2/2] Generating real data animations...
py flow_animator.py
echo.

echo ========================================
echo   Done! Check charts\ folder
echo ========================================
dir charts 2>nul
echo.
pause
