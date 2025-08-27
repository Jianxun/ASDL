from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance


def make_file_with_modules():
    return ASDLFile(
        file_info=FileInfo(),
        modules={
            "NDEV": Module(spice_template="M ..."),
            "TOP": Module(instances={}),
        },
    )


def test_is_primitive_instance():
    f = make_file_with_modules()
    inst = Instance(model="NDEV", mappings={})
    assert inst.is_primitive_instance(f) is True
    assert inst.is_hierarchical_instance(f) is False


def test_is_hierarchical_instance():
    f = make_file_with_modules()
    inst = Instance(model="TOP", mappings={})
    assert inst.is_primitive_instance(f) is False
    assert inst.is_hierarchical_instance(f) is True


def test_instance_unknown_model():
    f = make_file_with_modules()
    inst = Instance(model="NOPE", mappings={})
    assert inst.is_primitive_instance(f) is False
    assert inst.is_hierarchical_instance(f) is False


