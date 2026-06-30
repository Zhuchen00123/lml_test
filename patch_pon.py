path = '/tmp/linux-lmi/drivers/power/reset/qcom-pon.c'
code = open(path).read()

# Add new defines after PON_SOFT_RB_SPARE
old_def = '#define PON_SOFT_RB_SPARE\t\t0x8f'
new_defs = '#define PON_SOFT_RB_SPARE\t\t0x8f\n#define PON_PS_HOLD_RESET_CTL\t\t0x88a\n#define PON_PS_HOLD_RESET_CTL2\t\t0x88b\n\nstatic struct qcom_pon *sys_pon;'
code = code.replace(old_def, new_defs)

# Add poweroff function before probe
poweroff_fn = '''static void qcom_pon_power_off(void)
{
\tif (!sys_pon || !sys_pon->regmap)
\t\treturn;

\t/* Write to PS_HOLD_RESET_CTL to trigger poweroff */
\tregmap_write(sys_pon->regmap,
\t\t     sys_pon->baseaddr + PON_PS_HOLD_RESET_CTL, 0x1);
\tmdelay(1000);
\tpr_emerg("PON poweroff failed, trying fallback\\n");
\tregmap_write(sys_pon->regmap,
\t\t     sys_pon->baseaddr + PON_PS_HOLD_RESET_CTL, 0x80);
}

'''
old_probe = 'static int qcom_pon_probe(struct platform_device *pdev)'
code = code.replace(old_probe, poweroff_fn + old_probe)

# Add system-power-controller check
old_drvdata = '\tplatform_set_drvdata(pdev, pon);'
new_drvdata = '\tplatform_set_drvdata(pdev, pon);\n\n\tif (of_device_is_system_power_controller(pdev->dev.of_node)) {\n\t\tsys_pon = pon;\n\t\tpm_power_off = qcom_pon_power_off;\n\t\tdev_info(&pdev->dev, "registered as system power controller\\n");\n\t}'
code = code.replace(old_drvdata, new_drvdata)

open(path, 'w').write(code)
print('Patched')
