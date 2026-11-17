# Cudy WR1300E v2 — исправленная сборка OpenWrt 25.12.6 (попытка №2)

## Диагностика предыдущей попытки

`WR1300E_build_diagnostics.zip` показал: сборка завершила компиляцию образа,
но сравнение ABI завершилось ошибкой (`c6e498a9f9e2504551704be0f9004211`
вместо официального `aa81475ddbdbcc69877f69037ae40cd8`).

Причина в предыдущем `create_config.py`: вместо полного официального `config.buildinfo`
он оставлял только часть настроек, менял режим многопрофильной сборки на single-profile,
выключал `CONFIG_BUILDBOT`, `CONFIG_ALL_NONSHARED`, `CONFIG_COLLECT_KERNEL_DEBUG`,
`CONFIG_TARGET_PER_DEVICE_ROOTFS` и другие флаги сборочного сервера.
В OpenWrt `vermagic` зависит от сгенерированного Kconfig ядра, а не только от версии Linux.

## Что изменено

1. Используется **полный** официальный `config.buildinfo` от `ramips/mt7621`,
   проверяется его SHA256.
2. Добавляется только новый профиль в формате `CONFIG_TARGET_DEVICE_...=y`,
   без выбора `CONFIG_TARGET_ramips_mt7621_DEVICE_...` (single-profile).
3. Сохраняются `BUILDBOT`, `ALL_NONSHARED`, `ALL_KMODS`, `COLLECT_KERNEL_DEBUG`,
   `TARGET_ALL_PROFILES`, `TARGET_PER_DEVICE_ROOTFS` и `KERNEL_KALLSYMS=n`.
4. Чтобы не создавать сотни прошивок, патчится **только механизм отбора выходных образов**
   (`include/image.mk`). Конфигурация ядра не изменяется намеренно.
5. Сначала собирается ядро и сравнивается его фактический `.vermagic` с официальным.
   При несовпадении выполнение прекращается, все диагностические файлы сохраняются.
6. В прошивке остаются штатные пакеты OpenWrt и LuCI. AmneziaWG, PBR, Podkop,
   EasyTier и другие сторонние модули НЕ добавляются.

**Осторожно:** пока нет результата новой GitHub Actions сборки, совпадение ABI
не подтверждено. Даже совпавший hash сам по себе не означает тестирования роутера.

## Запуск из нового или существующего GitHub-репозитория

1. Загрузите содержимое ZIP в **корень репозитория**, заменив одноимённые файлы
   (`.github/workflows/build.yml`, `build.sh`, `create_config.py` и т. п.).
2. В GitHub откройте Actions → `WR1300E v2 - OpenWrt 25.12.6 - Fix official kernel ABI`
   → Run workflow.
3. Если сборка упадёт, скачайте `WR1300E_ABI_FIX_V2_diagnostics` и передайте архив
   для анализа. Он содержит `early-abi-result.json`, `kernel-vermagic.txt` и
   `kernel-config.set` (если сгенерирован).
4. В случае успеха скачайте `WR1300E_v2_25.12.6_OFFICIAL_ABI_UNTESTED` и
   проверьте `abi-result.json`: `matches_official_abi: true`.

## После сборки и до установки прошивки

- Убедиться, что модель — **Cudy WR1300E v2**, а не WR1300 v2/v3.
- Сохранить резервные копии уникальных разделов `factory`, `bdinfo`, загрузчика,
  параметры /etc, SSH/VPN-ключи **локально**, не публиковать их в GitHub.
- Проверить `/proc/mtd`, `ubus call system board`, `sysupgrade -T` и метод
  восстановления. **Не использовать `sysupgrade -F` без отдельной проверки.**
- DTS модели из предыдущего комплекта реконструирован по исходным материалам;
  аппаратная совместимость не подтверждена испытаниями.

## APK после установки

После аппаратно проверенной прошивки и подтверждённого ABI:

```sh
apk update
apk add kmod-tun
```

Это пример загрузки официального модуля TUN, **не** инструкция прошивать
непроверенный образ. AmneziaWG и прочие сторонние модули потребуют
дополнительной проверки доступности в репозитории и совместимости.

## Источники и механизм

- OpenWrt 25.12.6 `config.buildinfo`:
  https://downloads.openwrt.org/releases/25.12.6/targets/ramips/mt7621/config.buildinfo
- Официальные APK пакеты:
  https://downloads.openwrt.org/releases/25.12.6/targets/ramips/mt7621/kmods/
- Расчёт `.vermagic` (`grep '=[ym]' | sort | md5`):
  https://git.openwrt.org/openwrt/openwrt/tree/include/kernel-defaults.mk?h=v25.12.6

## Состав репозитория

`build.sh`, `create_config.py`, `limit_images.py`, `check_early_abi.py`,
`check_abi.py`, `verify_image.py`, `apply_wr1300e.py`, `device/...dts`,
`.github/workflows/build.yml`, `README_RU.md`.
