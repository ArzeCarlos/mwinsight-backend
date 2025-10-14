from test.SnmpModuleTest import testSnmp

def main():
    community = "public"
    host = "demo.pysnmp.com"

    print("\nTest con un OID de tipo entero:")
    testSnmp.testSnmpModule(
        oid="1.3.6.1.2.1.1.7.0",
        host=host,
        value_type="1",
        community=community,
        unit="",
        multiplication=1,
        division=1,
    )

    print("\nTest con un OID de tipo flotante:")
    testSnmp.testSnmpModule(
        oid="1.3.6.1.2.1.1.3.0",
        host=host,
        value_type="1",
        community=community,
        unit="seconds",
        multiplication=1,
        division=100,
    )

    print("\nTest con un OID de tipo cadena:")
    testSnmp.testSnmpModule(
        oid="1.3.6.1.2.1.1.1.0",
        host=host,
        value_type="1",
        community=community,
        unit="",
        multiplication=1,
        division=1
    )

if __name__ == "__main__":
    main()
