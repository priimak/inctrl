import pytest

from inctrl import Duration, TimeUnit


def test_duration_instantiation():
    with pytest.raises(Exception):
        Duration.value_of("1 z")  # invalid time unit "z"

    with pytest.raises(Exception):
        Duration.value_of("1 Ks")  # mixed case for time unit is not supported

    assert Duration.value_of("1 ks") is not None
    assert Duration.value_of("1 KS") is not None
    assert Duration.value_of("1 s") is not None
    assert Duration.value_of("1 S") is not None
    assert Duration.value_of("1 ms") is not None
    assert Duration.value_of("1 MS") is not None
    assert Duration.value_of("1 us") is not None
    assert Duration.value_of("1 US") is not None
    assert Duration.value_of("1 ns") is not None
    assert Duration.value_of("1 NS") is not None

    # absense of space and leading and trailing space should not matter
    assert Duration.value_of(" 1ks ") is not None
    assert Duration.value_of(" 1KS  ") is not None
    assert Duration.value_of(" 1s  ") is not None
    assert Duration.value_of(" 1S   ") is not None
    assert Duration.value_of(" 1ms  ") is not None
    assert Duration.value_of(" 1MS   ") is not None
    assert Duration.value_of(" 1us  ") is not None
    assert Duration.value_of(" 1US  ") is not None
    assert Duration.value_of(" 1ns   ") is not None
    assert Duration.value_of(" 1NS  ") is not None

    # value_of(...) should also take instance of Duration class
    assert Duration.value_of(Duration.value_of("1 s")).to_float("s") == 1


def test_duration_equality():
    assert Duration.value_of("1s") == Duration.value_of("1s")
    assert Duration.value_of("1s") == Duration.value_of("1000 ms")
    assert Duration.value_of("1s") != Duration.value_of("1001 ms")

    # comparing Duration with objects that are not Duration should raise RuntimeError
    with pytest.raises(Exception):
        assert Duration.value_of("1s") == 1.0

    with pytest.raises(Exception):
        assert 1 == Duration.value_of("1s")


def test_duration_comparison():
    assert Duration.value_of("1s") >= Duration.value_of("1 s")
    assert Duration.value_of("1s") <= Duration.value_of("1 s")
    assert (Duration.value_of("1s") > Duration.value_of("1 s")) == False
    assert Duration.value_of("1.1 s") >= Duration.value_of("1000000 us")
    assert (Duration.value_of("1.1 s") < Duration.value_of("1000000 us")) == False
    assert Duration.value_of("0.9 s") < Duration.value_of("1000000 us")

    with pytest.raises(Exception):
        assert Duration.value_of("1s") >= "1s"
    with pytest.raises(Exception):
        assert Duration.value_of("1s") <= "1s"
    with pytest.raises(Exception):
        assert Duration.value_of("1s") > "1s"
    with pytest.raises(Exception):
        assert Duration.value_of("1s") >= "1s"
    with pytest.raises(Exception):
        assert Duration.value_of("1s") < "1s"


def test_duration_math_ops():
    assert Duration.value_of("1s") * 2 == Duration.value_of("2 s")
    assert 3.1 * Duration.value_of("1s") == Duration.value_of("3.1 s")
    assert Duration.value_of("1s") / 2 == Duration.value_of("0.5 s")
    assert Duration.value_of("1s") + Duration.value_of("2 ms") == Duration.value_of("1002 ms")
    assert Duration.value_of("1ms") - Duration.value_of("2 ms") == Duration.value_of("-1 ms")
    assert abs(Duration.value_of("-2 ns")) == Duration.value_of("2 ns")


def test_duration_optimize():
    assert Duration.value_of("1002ns").optimize().time_unit == TimeUnit.US
    assert Duration.value_of("999ns").optimize().time_unit == TimeUnit.NS
    assert Duration.value_of("1002ns").optimize() == Duration.value_of("0.001002 ms")
