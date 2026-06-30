dts_path = '/tmp/linux-lmi-pmos/arch/arm64/boot/dts/qcom/sm8250-xiaomi-lmi.dts'
dts = open(dts_path).read()

old = '&pm8150b_pon {\n\tstatus = "okay";\n\tsystem-power-controller;\n};\n'
new = '&pon {\n\tsystem-power-controller;\n};\n'

if old in dts:
    dts = dts.replace(old, new)
    open(dts_path, 'w').write(dts)
    print('Fixed: replaced pm8150b_pon with pon')
else:
    print('Old pattern not found!')
    # Check what's there
    idx = dts.find('&pon')
    print(dts[idx:idx+60])
