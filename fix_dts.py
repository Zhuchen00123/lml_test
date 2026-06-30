dts_path = '/tmp/linux-lmi-pmos/arch/arm64/boot/dts/qcom/sm8250-xiaomi-lmi.dts'
dts = open(dts_path).read()

insert = '''&pm8150b_pon {
	status = "okay";
	system-power-controller;
};

'''
pos = dts.find('&pon_pwrkey')
if pos >= 0:
    dts = dts[:pos] + insert + dts[pos:]
    open(dts_path, 'w').write(dts)
    print('OK offset', pos)
else:
    print('NOT FOUND')
