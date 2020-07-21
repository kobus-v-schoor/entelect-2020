from sloth.enums import max_speed, next_speed, prev_speed, Speed, boost_speed

class TestEnumFuncs:
    def test_max_speed(self):
        assert max_speed(0) == Speed.MAX_SPEED.value
        assert max_speed(1) == Speed.MAX_SPEED.value
        assert max_speed(2) == Speed.SPEED_3.value
        assert max_speed(3) == Speed.SPEED_2.value
        assert max_speed(4) == Speed.SPEED_1.value
        assert max_speed(5) == Speed.MIN_SPEED.value

        assert max_speed(6) == Speed.MIN_SPEED.value
        assert max_speed(10) == Speed.MIN_SPEED.value

    def test_next_speed(self):
        assert next_speed(Speed.SPEED_1.value) == Speed.SPEED_2.value
        assert next_speed(Speed.SPEED_3.value) == Speed.MAX_SPEED.value
        assert next_speed(Speed.SPEED_3.value, 2) == Speed.SPEED_3.value
        assert next_speed(Speed.SPEED_3.value, 3) == Speed.SPEED_2.value
        assert next_speed(Speed.SPEED_3.value, 4) == Speed.SPEED_1.value
        assert next_speed(Speed.SPEED_1.value, 4) == Speed.SPEED_1.value

    def test_boost_speed(self):
        assert boost_speed(0) == Speed.BOOST_SPEED.value
        for i in range(1, 7):
            assert boost_speed(i) == max_speed(i)
