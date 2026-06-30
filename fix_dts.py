dts_path = '/tmp/linux-lmi/arch/arm64/boot/dts/qcom/sm8250-xiaomi-lmi.dts'
dts = open(dts_path).read()

old = '&pm8150b_pon {\n\tstatus = "okay";\n\tsystem-power-controller;\n};\n'
new = '&pon {\n\tsystem-power-controller;\n};\n'

if old in dts:
    dts = dts.replace(old, new)
    open(dts_path, 'w').write(dts)
    print('Fixed: replaced pm8150b_pon with pon')
else:
    # First time - insert before &pon_pwrkey
    insert = '&pon {\n\tsystem-power-controller;\n};\n\n'
    pos = dts.find('&pon_pwrkey')
    if pos >= 0:
        dts = dts[:pos] + insert + dts[pos:]
        open(dts_path, 'w').write(dts)
        print('Inserted system-power-controller at offset', pos)
    else:
        print('ERROR: &pon_pwrkey not found')
