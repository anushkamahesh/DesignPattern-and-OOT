import pytest

from src.domain.locations.config_builder import LocationConfigBuilder
from src.domain.locations.errors import ConfigurationError


def _valid():
    return (
        LocationConfigBuilder()
        .set_name("North House")
        .add_zone("Zone A", 0.2, 0.6, {"start": "06:00"})
    )


def test_success_path():
    config = _valid().add_zone("Zone B", 0.3, 0.7).build()
    assert config.location.name == "North House"
    assert [z.name for z in config.location.zones] == ["Zone A", "Zone B"]
    assert config.location.id is None
    assert all(z.id is None for z in config.location.zones)


def test_build_is_deterministic():
    assert _valid().build() == _valid().build()


@pytest.mark.parametrize("name", ["", "   "])
def test_missing_location_name(name):
    b = LocationConfigBuilder().set_name(name).add_zone("Z", 0.2, 0.6)
    with pytest.raises(ConfigurationError):
        b.build()


def test_location_name_never_set():
    b = LocationConfigBuilder().add_zone("Z", 0.2, 0.6)
    with pytest.raises(ConfigurationError):
        b.build()


def test_no_zones():
    with pytest.raises(ConfigurationError):
        LocationConfigBuilder().set_name("A").build()


@pytest.mark.parametrize("low,high", [(0.6, 0.2), (0.5, 0.5)])
def test_invalid_threshold_ordering(low, high):
    with pytest.raises(ConfigurationError):
        LocationConfigBuilder().set_name("A").add_zone("Z", low, high)


@pytest.mark.parametrize("low,high", [(-0.1, 0.5), (0.1, 1.1)])
def test_thresholds_out_of_range(low, high):
    with pytest.raises(ConfigurationError):
        LocationConfigBuilder().set_name("A").add_zone("Z", low, high)


def test_empty_zone_name():
    with pytest.raises(ConfigurationError):
        LocationConfigBuilder().set_name("A").add_zone("  ", 0.2, 0.6)


def test_duplicate_zone_names_rejected():
    b = _valid().add_zone("zone a", 0.1, 0.5)
    with pytest.raises(ConfigurationError):
        b.build()


def test_builder_cannot_attach_devices():
    assert not hasattr(LocationConfigBuilder, "add_device")


def test_configuration_error_is_value_error():
    assert issubclass(ConfigurationError, ValueError)