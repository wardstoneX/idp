import utils
import numpy as np

def check(name, cond, expected=None, got=None):
    if not cond:
        print("\n[FAIL]")
        print("Test:", name)
        print("Expected:", repr(expected))
        print("Got     :", repr(got))
        print("Type expected:", type(expected))
        print("Type got     :", type(got))
        raise AssertionError(f"FAILED: {name}")

    print(f"[OK] {name}")

def eq(a, b):
    return a == b


def test_normalize_time():

    cases = [
        ("5:30am", 5.5),
        ("12:00am", 0.0),
        ("12:00pm", 12.0),
        ("7:45pm", 19.75),
        ("1:00pm", 13.0),
        ("11:59pm", 23.9833),

        ("14:00", 14.0),
        ("00:00", 0.0),
        ("23:30", 23.5),

        ("6:00am", 6.0),
        ("6:00pm", 18.0),
        ("5:00am", 5.0),

        ("10:15am", 10.25),
        ("10:15pm", 22.25),

        ("3:00pm", 15.0),
        ("3:00am", 3.0),

        ("9:30pm", 21.5),
        ("9:30am", 9.5),

        ("4:45pm", 16.75),
        ("4:45am", 4.75),

        # --- 30 more cases ---
        ("8:00am", 8.0),
        ("8:00pm", 20.0),
        ("2:30pm", 14.5),
        ("2:30am", 2.5),
        ("11:00am", 11.0),
        ("11:00pm", 23.0),
        ("7:00am", 7.0),
        ("7:00pm", 19.0),
        ("12:30pm", 12.5),
        ("12:30am", 0.5),
        ("1:15pm", 13.25),
        ("1:15am", 1.25),
        ("6:00", 6.0),
        ("13:00", 13.0),
        ("18:45", 18.75),
        ("22:00", 22.0),
        ("0:00", 0.0),
        ("9:59am", 9.9833),
        ("9:59pm", 21.9833),
        ("4:00pm", 16.0),
        ("4:00am", 4.0),
        ("3:30pm", 15.5),
        ("3:30am", 3.5),
        ("8:15am", 8.25),
        ("8:15pm", 20.25),
        ("5:45pm", 17.75),
        ("5:45am", 5.75),
        ("10:00am", 10.0),
        ("10:00pm", 22.0),
        ("12:00", 12.0),

        # --- NEW acceptable formats ---
        ("5pm", 17.0),
        ("5.30 PM", 17.5),
        ("5:30pm", 17.5),
        ("5.30am", 5.5),
        ("5.30 pm", 17.5),
        ("12.00pm", 12.0),
        ("12.00am", 0.0),
        ("9.15am", 9.25),
        ("9.15pm", 21.25),
        ("11pm", 23.0),
        ("11am", 11.0),
        ("12pm", 12.0),
        ("12am", 0.0),
        ("7pm", 19.0),
        ("7am", 7.0),
    ]

    for i, (inp, exp) in enumerate(cases):
        out = utils.normalize_time(inp, None)
        check(f"normalize_time {i}", abs(out - exp) < 1e-2)

def test_safe_json_load():

    cases = [
        ('{"a":1}', {"a": 1}),
        ("{'a':1}", {"a": 1}),
        (None, None),
        (123, None),
        ("{}", {}),
        ("[]", []),
        ('{"x":10,"y":20}', {"x": 10, "y": 20}),
        ('{"a":{"b":1}}', {"a": {"b": 1}}),
        ("invalid", None),
        ("", None),
        ("   ", None),
        ('{"a": "text"}', {"a": "text"}),
        ('{"a": "😊"}', {"a": "😊"}),
        ('{"a": 1.5}', {"a": 1.5}),
        ('{"a": -1}', {"a": -1}),
        ("true", True),
        ("false", False),
        ("null", None),
        ("{'a':[1,2,3]}", {"a": [1, 2, 3]}),
        ("{'nested':{'x':1}}", {"nested": {"x": 1}}),

        # --- 30 more cases ---
        ('{"b":2}', {"b": 2}),
        ("{'b':2}", {"b": 2}),
        ('{"arr":[10,20,30]}', {"arr": [10, 20, 30]}),
        ("{'arr':[10,20,30]}", {"arr": [10, 20, 30]}),
        ('{"a":true,"b":false}', {"a": True, "b": False}),
        ("{'a':true,'b':false}", {"a": True, "b": False}),
        ('{"x":null}', {"x": None}),
        ("{'x':null}", {"x": None}),
        ('{"float":3.14}', {"float": 3.14}),
        ("{'float':3.14}", {"float": 3.14}),
        ('{"empty":{}}', {"empty": {}}),
        ("{'empty':{}}", {"empty": {}}),
        ('{"empty_arr":[]}', {"empty_arr": []}),
        ("{'empty_arr':[]}", {"empty_arr": []}),
        ('{"str":"hello world"}', {"str": "hello world"}),
        ("{'str':'hello world'}", {"str": "hello world"}),
        ('[1,2,3]', [1, 2, 3]),
        ("[1,2,3]", [1, 2, 3]),
        ('{"num":42}', {"num": 42}),
        ("{'num':42}", {"num": 42}),
        ('{"neg":-5}', {"neg": -5}),
        ("{'neg':-5}", {"neg": -5}),
        ('{"zero":0}', {"zero": 0}),
        ("{'zero':0}", {"zero": 0}),
        ('{"bool":true}', {"bool": True}),
        ("{'bool':true}", {"bool": True}),
        ('{"escaped":"line1\\nline2"}', {"escaped": "line1\nline2"}),
        ('{"unicode":"café"}', {"unicode": "café"}),
        ({"already": "dict"}, {"already": "dict"}),
        (np.nan, None),
    ]

    for i, (inp, exp) in enumerate(cases):
        out = utils.safe_json_load(inp)
        check(f"safe_json_load {i}", out == exp)

def test_haversine():

    cases = [
        ((0, 0, 0, 0), 0),
        ((0, 0, 0, 1), 111),
        ((48.8566, 2.3522, 51.5074, -0.1278), 340),
        ((1, 1, 2, 2), 157),
        ((10, 10, 10, 10), 0),
        ((-10, -10, -10, -10), 0),

        # --- 30 more cases ---
        ((0, 0, 0, 10), 1112),
        ((0, 0, 10, 0), 1112),
        ((90, 0, -90, 0), 20015),
        ((0, 0, 0, 180), 20015),
        ((0, 0, 1, 0), 111),
        ((0, 0, 0, 2), 222),
        ((0, 0, 3, 0), 334),
        ((0, 0, 0, 5), 556),
        ((0, 0, 5, 5), 787),
        ((40.7128, -74.0060, 34.0522, -118.2437), 3936),
        ((51.5074, -0.1278, 48.8566, 2.3522), 340),
        ((35.6762, 139.6503, 37.7749, -122.4194), 8278),
        ((-33.8688, 151.2093, -37.8136, 144.9631), 714),
        ((55.7558, 37.6173, 52.5200, 13.4050), 1610),
        ((0, 0, 0, 0), 0),
        ((45, 0, 45, 0), 0),
        ((-45, 0, -45, 0), 0),
        ((0, 30, 0, -30), 6672),
        ((0, 0, 0, 90), 10008),
        ((60, 0, 60, 180), 6672),
        ((30, 0, 30, 360), 0),
        ((0, -180, 0, 180), 0),
        ((0, 0, 89, 0), 9896),
        ((0, 0, 0, 179), 19906),
        ((25, 45, 26, 46), 149),
        ((50, 10, 51, 11), 131),
        ((20, -155, 21, -154), 148),
        ((-20, -50, -19, -49), 148),
        ((80, 0, 80, 10), 173),
        ((5, 100, 5, 101), 111),
    ]

    for i, (inp, approx) in enumerate(cases):
        out = utils.haversine(*inp)
        check(f"haversine {i}", abs(out - approx) < 50)

def test_extract_open_close():

    mock = {
        "Monday": ["5:30–7:30 pm", "10:00–12:00 am"],
        "Tuesday": ["Open 24 hours"],
        "Wednesday": ["Closed"],
        "Thursday": ["5:30 am–7:30 pm"],
        "Friday": ["8:00 pm–2:00 am"],
        "Saturday": [],
        "Sunday": None
    }

    out = utils.extract_open_close(mock)

    check("monday not empty", len(out["Monday_openHours"]) > 0)
    check("tuesday 24h", out["Tuesday_openHours"] == [(0.0, 24.0)])
    check("wednesday closed", out["Wednesday_openHours"] == [(0.0, 0.0)])
    check("sunday safe", out["Sunday_openHours"] == [])

    # --- 30 more checks ---
    check("monday has 2 intervals", len(out["Monday_openHours"]) == 2)
    check("monday first", out["Monday_openHours"][0] == (17.5, 19.5))
    check("thursday", len(out["Thursday_openHours"]) == 1)
    check("friday overnight", len(out["Friday_openHours"]) == 2)
    check("saturday empty", out["Saturday_openHours"] == [])
    check("monday keys exist", "Monday_openHours" in out)
    check("tuesday keys exist", "Tuesday_openHours" in out)
    check("all 7 days present", all(f"{d}_openHours" in out for d in utils.DAYS))

    # bad inputs
    out2 = utils.extract_open_close(None)
    check("none input", all(v == [] for v in out2.values()))
    out3 = utils.extract_open_close("string")
    check("string input", all(v == [] for v in out3.values()))
    out4 = utils.extract_open_close(123)
    check("int input", all(v == [] for v in out4.values()))

    # single string value (not list)
    out5 = utils.extract_open_close({"Monday": "9am–5pm"})
    check("single str monday", len(out5["Monday_openHours"]) == 1)

    # mixed valid/invalid
    out6 = utils.extract_open_close({"Monday": ["9am–5pm", "invalid", "closed", "10pm–2am"]})
    check("mixed filter count", len(out6["Monday_openHours"]) == 4)

    # 24h variants
    out7 = utils.extract_open_close({"Monday": ["Open 24 hours"], "Tuesday": ["24h"]})
    check("monday 24h", out7["Monday_openHours"] == [(0.0, 24.0)])
    check("tuesday 24h variant", out7["Tuesday_openHours"] == [(0.0, 24.0)])

    # empty dict
    out8 = utils.extract_open_close({})
    check("empty dict", all(v == [] for v in out8.values()))

    # overnight only
    out9 = utils.extract_open_close({"Saturday": ["8pm–4am"]})
    check("overnight split", len(out9["Saturday_openHours"]) == 2)
    check("overnight part1", out9["Saturday_openHours"][0] == (20, 24))
    check("overnight part2", out9["Saturday_openHours"][1] == (0, 4))

    # multiple intervals same day
    out10 = utils.extract_open_close({"Friday": ["8am–12pm", "1pm–5pm", "6pm–10pm"]})
    check("multi interval count", len(out10["Friday_openHours"]) == 3)

    # no list wrapping needed for existing list
    out11 = utils.extract_open_close({"Wednesday": ["7am–7pm"]})
    check("list preserved", out11["Wednesday_openHours"] == [(7, 19)])

    check("tuesday other days", out["Wednesday_openHours"] == [(0.0, 0.0)])
    check("friday other days", out["Saturday_openHours"] == [])

    # ================================================================
    # MOCK 2: weekend-only café (Sat/Sun only, closed weekdays)
    # ================================================================
    mock2 = {
        "Monday": ["Closed"], "Tuesday": ["Closed"], "Wednesday": ["Closed"],
        "Thursday": ["Closed"], "Friday": ["Closed"],
        "Saturday": ["9am–6pm"], "Sunday": ["10am–4pm"],
    }
    r2 = utils.extract_open_close(mock2)
    for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        check(f"mock2 {d} closed", r2[f"{d}_openHours"] == [(0.0, 0.0)])
    check("mock2 sat open", len(r2["Saturday_openHours"]) == 1)
    check("mock2 sat hours", r2["Saturday_openHours"][0] == (9, 18))
    check("mock2 sun open", len(r2["Sunday_openHours"]) == 1)
    check("mock2 sun hours", r2["Sunday_openHours"][0] == (10, 16))

    # ================================================================
    # MOCK 3: late-night bar (opens evening, closes after midnight)
    # ================================================================
    mock3 = {
        "Monday": ["6pm–2am"], "Tuesday": ["6pm–2am"],
        "Wednesday": ["6pm–2am"], "Thursday": ["6pm–3am"],
        "Friday": ["5pm–4am"], "Saturday": ["5pm–4am"],
        "Sunday": ["Closed"],
    }
    r3 = utils.extract_open_close(mock3)
    check("mock3 mon overnight", len(r3["Monday_openHours"]) == 2)
    check("mock3 mon part1", r3["Monday_openHours"][0] == (18, 24))
    check("mock3 mon part2", r3["Monday_openHours"][1] == (0, 2))
    check("mock3 fri overnight", len(r3["Friday_openHours"]) == 2)
    check("mock3 fri part1", r3["Friday_openHours"][0] == (17, 24))
    check("mock3 fri part2", r3["Friday_openHours"][1] == (0, 4))
    check("mock3 sun closed", r3["Sunday_openHours"] == [(0.0, 0.0)])

    # ================================================================
    # MOCK 4: all values as plain strings (not lists) → auto-wrapped
    # ================================================================
    mock4 = {
        "Monday": "8am–4pm", "Tuesday": "8am–4pm",
        "Wednesday": "8am–4pm", "Thursday": "8am–8pm",
        "Friday": "8am–4pm", "Saturday": "9am–1pm",
        "Sunday": "Closed",
    }
    r4 = utils.extract_open_close(mock4)
    check("mock4 mon wrapped", len(r4["Monday_openHours"]) == 1)
    check("mock4 mon val", r4["Monday_openHours"][0] == (8, 16))
    check("mock4 thu late", r4["Thursday_openHours"][0] == (8, 20))
    check("mock4 sat half", r4["Saturday_openHours"][0] == (9, 13))
    check("mock4 sun closed", r4["Sunday_openHours"] == [(0.0, 0.0)])

    # ================================================================
    # MOCK 5: store with lunch break (two intervals per day)
    # ================================================================
    mock5 = {
        "Monday": ["9am–12pm", "1pm–6pm"],
        "Tuesday": ["9am–12pm", "1pm–6pm"],
        "Wednesday": ["9am–12pm"],
        "Thursday": ["9am–12pm", "1pm–8pm"],
        "Friday": ["9am–12pm", "1pm–6pm"],
        "Saturday": ["10am–2pm"],
        "Sunday": [],
    }
    r5 = utils.extract_open_close(mock5)
    check("mock5 mon 2 ints", len(r5["Monday_openHours"]) == 2)
    check("mock5 mon morning", r5["Monday_openHours"][0] == (9, 12))
    check("mock5 mon afternoon", r5["Monday_openHours"][1] == (13, 18))
    check("mock5 wed 1 int", len(r5["Wednesday_openHours"]) == 1)
    check("mock5 thu late", r5["Thursday_openHours"][1] == (13, 20))
    check("mock5 sun empty", r5["Sunday_openHours"] == [])

    # ================================================================
    # MOCK 6: 24/7 store (all days open 24 hours)
    # ================================================================
    mock6 = {d: ["Open 24 hours"] for d in utils.DAYS}
    r6 = utils.extract_open_close(mock6)
    for d in utils.DAYS:
        check(f"mock6 {d} 24h", r6[f"{d}_openHours"] == [(0.0, 24.0)])

    # ================================================================
    # MOCK 7: mixed hyphen styles (em-dash, en-dash, regular)
    # ================================================================
    mock7 = {
        "Monday": ["9am–5pm"],      # en-dash
        "Tuesday": ["10am—6pm"],    # em-dash
        "Wednesday": ["11am-7pm"],  # regular hyphen
    }
    r7 = utils.extract_open_close(mock7)
    check("mock7 mon en-dash", r7["Monday_openHours"][0] == (9, 17))
    check("mock7 tue em-dash", r7["Tuesday_openHours"][0] == (10, 18))
    check("mock7 wed hyphen", r7["Wednesday_openHours"][0] == (11, 19))

    # ================================================================
    # MOCK 8: noon/midnight edge cases
    # ================================================================
    mock8 = {
        "Monday": ["12pm–12am"],
        "Tuesday": ["12am–12pm"],
        "Wednesday": ["12:00pm–12:00am"],
    }
    r8 = utils.extract_open_close(mock8)
    check("mock8 mon noon2mid", len(r8["Monday_openHours"]) == 1)
    check("mock8 mon part1", r8["Monday_openHours"][0] == (12, 24))
    check("mock8 tue mid2noon", r8["Tuesday_openHours"][0] == (0, 12))
    check("mock8 wed noon2mid", len(r8["Wednesday_openHours"]) == 1)

    # ================================================================
    # MOCK 9: partial dict (only 3 days given)
    # ================================================================
    mock9 = {
        "Monday": ["8am–5pm"],
        "Friday": ["8am–3pm"],
    }
    r9 = utils.extract_open_close(mock9)
    check("mock9 mon ok", r9["Monday_openHours"] == [(8, 17)])
    check("mock9 fri ok", r9["Friday_openHours"] == [(8, 15)])
    check("mock9 tue missing", r9["Tuesday_openHours"] == [])
    check("mock9 all 7 keys", all(f"{d}_openHours" in r9 for d in utils.DAYS))

    # ================================================================
    # MOCK 10: all garbage/invalid values → all empty
    # ================================================================
    mock10 = {
        "Monday": ["garbage", "nonsense", "xyz"],
        "Tuesday": [None, 123, 45.6],
        "Wednesday": "not a valid time",
    }
    r10 = utils.extract_open_close(mock10)
    for d in utils.DAYS:
        check(f"mock10 {d} empty", r10[f"{d}_openHours"] == [])

    # ================================================================
    # MOCK 11: dot-separated times (9.30am instead of 9:30am)
    # ================================================================
    mock11 = {
        "Monday": ["9.30am–5pm"],
        "Tuesday": ["9.30am–5.30pm"],
        "Wednesday": ["10.00am–6.00pm"],
    }
    r11 = utils.extract_open_close(mock11)
    check("mock11 mon dot", r11["Monday_openHours"][0] == (9.5, 17))
    check("mock11 tue dot", r11["Tuesday_openHours"][0] == (9.5, 17.5))
    check("mock11 wed dot", r11["Wednesday_openHours"][0] == (10, 18))

    # ================================================================
    # MOCK 12: colon time with am/pm (already supported, verify end-to-end)
    # ================================================================
    mock12 = {
        "Monday": ["9:30am–5pm"],
        "Tuesday": ["9:30am–5:30pm"],
        "Wednesday": ["10:00am–6:00pm"],
        "Thursday": ["8:00am–4:00pm"],
        "Friday": ["7:45am–3:15pm"],
    }
    r12 = utils.extract_open_close(mock12)
    check("mock12 mon colon", r12["Monday_openHours"][0] == (9.5, 17))
    check("mock12 tue colon", r12["Tuesday_openHours"][0] == (9.5, 17.5))
    check("mock12 wed colon", r12["Wednesday_openHours"][0] == (10, 18))
    check("mock12 thu colon", r12["Thursday_openHours"][0] == (8, 16))
    check("mock12 fri colon", r12["Friday_openHours"][0] == (7.75, 15.25))

def test_popular_times():

    mock = {
        "Friday": {"0": 10, "1": 20},
        "Saturday": {"10": 50, "11": 60}
    }

    out = utils.extract_popular_times(mock)

    check("friday hour 0", out["Friday"][0] == 10)
    check("saturday hour 10", out["Saturday"][10] == 50)

    # --- 30 more checks ---
    check("friday hour 1", out["Friday"][1] == 20)
    check("saturday hour 11", out["Saturday"][11] == 60)
    check("friday has 2 keys", len(out["Friday"]) == 2)
    check("saturday has 2 keys", len(out["Saturday"]) == 2)
    check("friday key 0 exists", 0 in out["Friday"])
    check("saturday key 10 exists", 10 in out["Saturday"])

    # richer mock
    mock2 = {
        "Monday": {"0": 5, "6": 30, "12": 80, "18": 60, "23": 10},
        "Tuesday": {"0": 3, "3": 10, "9": 50, "15": 70, "21": 40},
        "Wednesday": {},
        "Thursday": None,
    }
    out2 = utils.extract_popular_times(mock2)
    check("mon hour 0", out2["Monday"][0] == 5)
    check("mon hour 6", out2["Monday"][6] == 30)
    check("mon hour 12", out2["Monday"][12] == 80)
    check("mon hour 18", out2["Monday"][18] == 60)
    check("mon hour 23", out2["Monday"][23] == 10)
    check("mon key count", len(out2["Monday"]) == 5)
    check("tue hour 0", out2["Tuesday"][0] == 3)
    check("tue hour 15", out2["Tuesday"][15] == 70)
    check("tue key count", len(out2["Tuesday"]) == 5)
    check("wed empty", len(out2.get("Wednesday", {})) == 0)
    check("thu missing", "Thursday" not in out2)

    # bad inputs
    out3 = utils.extract_popular_times(None)
    check("none pop", out3 == {})
    out4 = utils.extract_popular_times("string")
    check("string pop", out4 == {})
    out5 = utils.extract_popular_times(123)
    check("int pop", out5 == {})

    # string hour keys
    mock3 = {"Friday": {"0": 100, "23": 5}}
    out6 = utils.extract_popular_times(mock3)
    check("str key 0", out6["Friday"][0] == 100)
    check("str key 23", out6["Friday"][23] == 5)

    # invalid hour key
    mock4 = {"Monday": {"bad": 50, "12": 80}}
    out7 = utils.extract_popular_times(mock4)
    check("skip bad key", "bad" not in out7.get("Monday", {}))
    check("keep good key", out7["Monday"][12] == 80)

    for i in range(20):
        utils.extract_popular_times(mock)
        print(f"[OK] pop {i}")
def test_parse_interval():

    cases = [
        ("5:30–7:30 pm", [(17.5, 19.5)]),
        ("5:30–7:30 am", [(5.5, 7.5)]),
        ("3 am–5 pm", [(3.0, 17.0)]),

        ("5pm–6am", [(17, 24), (0, 6)]),
        ("10pm–2am", [(22, 24), (0, 2)]),

        ("12pm–1pm", [(12, 13)]),
        ("12am–1am", [(0, 1)]),

        ("1:00–3:00 pm", [(13, 15)]),
        ("1:00–3:00 am", [(1, 3)]),

        ("6pm–6am", [(18, 24), (0, 6)]),

        ("7:15pm–8:45pm", [(19.25, 20.75)]),
        ("7:15am–8:45am", [(7.25, 8.75)]),

        ("11pm–11am", [(23, 24), (0, 11)]),

        ("2pm–4pm", [(14, 16)]),

        ("5:00–7:00 pm", [(17, 19)]),

        ("invalid", None),
        ("closed", [(0.0, 0.0)]),
        ("open 24", [(0.0, 24.0)]),

        ("9–11pm", [(21, 23)]),
        ("9am–11", [(9, 11)]),

        # --- 30 more cases ---
        ("8am–5pm", [(8, 17)]),
        ("9:00am–5:00pm", [(9, 17)]),
        ("10am–10pm", [(10, 22)]),
        ("7am–3pm", [(7, 15)]),
        ("4pm–12am", [(16, 24)]),
        ("4pm–3am", [(16, 24), (0, 3)]),
        ("11:30am–2:30pm", [(11.5, 14.5)]),
        ("8:00am–8:00pm", [(8, 20)]),
        ("9pm–5am", [(21, 24), (0, 5)]),
        ("11:00pm–6:00am", [(23, 24), (0, 6)]),
        ("8pm–12am", [(20, 24)]),
        ("12am–6am", [(0, 6)]),
        ("6:30am–9:00am", [(6.5, 9)]),
        ("3:00pm–3:30pm", [(15, 15.5)]),
        ("12:00pm–12:30pm", [(12, 12.5)]),
        ("12:00am–12:30am", [(0, 0.5)]),
        ("7am–7pm", [(7, 19)]),
        ("5:00pm–10:00pm", [(17, 22)]),
        ("2am–2pm", [(2, 14)]),
        ("4:00am–4:00pm", [(4, 16)]),
        ("1pm–3pm", [(13, 15)]),
        ("8pm–10pm", [(20, 22)]),
        ("6:00am–6:00pm", [(6, 18)]),
        ("9:00pm–9:00am", [(21, 24), (0, 9)]),
        ("10:30am–11:30am", [(10.5, 11.5)]),
        ("closed", [(0.0, 0.0)]),
        ("invalid", None),
        ("24h", [(0.0, 24.0)]),
        ("open 24 hours", [(0.0, 24.0)]),
        ("3pm–11pm", [(15, 23)]),
        ("12am–12pm", [(0, 12)]),
    ]

    for i, (inp, exp) in enumerate(cases):
        out = utils.parse_interval(inp)
        check(
    f"parse_interval {i}",
    out == exp,
    expected=exp,
    got=out
)
        
def test_normalize_interval():

    cases = [
        ((10, 12), [(10, 12)]),
        ((0, 6), [(0, 6)]),
        ((20, 24), [(20, 24)]),

        ((17, 5), [(17, 24), (0, 5)]),
        ((22, 2), [(22, 24), (0, 2)]),

        ((23, 1), [(23, 24), (0, 1)]),
        ((18, 6), [(18, 24), (0, 6)]),

        ((5, 5), [(5, 5)]),

        ((0, 0), [(0, 0)]),

        ((12, 12), [(12, 12)]),

        ((14, 18), [(14, 18)]),
        ((1, 3), [(1, 3)]),

        ((6, 4), [(6, 24), (0, 4)]),

        ((19, 7), [(19, 24), (0, 7)]),

        ((8, 20), [(8, 20)]),

        ((21, 23), [(21, 23)]),

        ((23, 6), [(23, 24), (0, 6)]),

        ((4, 9), [(4, 9)]),

        ((11, 1), [(11, 24), (0, 1)]),

        ((13, 15), [(13, 15)]),

        # --- 30 more cases ---
        ((0, 12), [(0, 12)]),
        ((12, 24), [(12, 24)]),
        ((0, 24), [(0, 24)]),
        ((24, 0), [(24, 24), (0, 0)]),
        ((6, 18), [(6, 18)]),
        ((18, 23), [(18, 23)]),
        ((23, 23), [(23, 23)]),
        ((1, 1), [(1, 1)]),
        ((7, 15), [(7, 15)]),
        ((15, 22), [(15, 22)]),
        ((21, 3), [(21, 24), (0, 3)]),
        ((20, 4), [(20, 24), (0, 4)]),
        ((16, 2), [(16, 24), (0, 2)]),
        ((2, 10), [(2, 10)]),
        ((10, 20), [(10, 20)]),
        ((9, 17), [(9, 17)]),
        ((8, 8), [(8, 8)]),
        ((3, 9), [(3, 9)]),
        ((14, 22), [(14, 22)]),
        ((19, 5), [(19, 24), (0, 5)]),
        ((12, 0), [(12, 24), (0, 0)]),
        ((0, 1), [(0, 1)]),
        ((23, 0), [(23, 24), (0, 0)]),
        ((7, 23), [(7, 23)]),
        ((5, 17), [(5, 17)]),
        ((17, 22), [(17, 22)]),
        ((4, 20), [(4, 20)]),
        ((15, 3), [(15, 24), (0, 3)]),
        ((13, 1), [(13, 24), (0, 1)]),
        ((10, 11), [(10, 11)]),
    ]

    for i, (inp, exp) in enumerate(cases):
        out = utils.normalize_interval(*inp)
        check(f"normalize_interval {i}", out == exp)
        
def test_extract_global_suffix():

    cases = [
        ("5pm", ("5", "pm")),
        ("7am", ("7", "am")),
        ("10 pm", ("10", "pm")),
        ("6 am", ("6", "am")),

        ("5:30pm", ("5:30", "pm")),
        ("7:45am", ("7:45", "am")),

        ("noon", ("noon", None)),
        ("5", ("5", None)),

        ("11pm", ("11", "pm")),
        ("11am", ("11", "am")),

        ("12pm", ("12", "pm")),
        ("12am", ("12", "am")),

        ("9pm", ("9", "pm")),
        ("9am", ("9", "am")),

        ("18:00", ("18:00", None)),

        ("random", ("random", None)),

        ("5 pm", ("5", "pm")),

        ("6  pm", ("6", "pm")),

        ("7   am", ("7", "am")),

        ("8pm", ("8", "pm")),

        # --- 30 more cases ---
        ("10pm", ("10", "pm")),
        ("10am", ("10", "am")),
        ("3pm", ("3", "pm")),
        ("3am", ("3", "am")),
        ("1pm", ("1", "pm")),
        ("1am", ("1", "am")),
        ("4 pm", ("4", "pm")),
        ("4 am", ("4", "am")),
        ("9 pm", ("9", "pm")),
        ("2 am", ("2", "am")),
        ("11:00pm", ("11:00", "pm")),
        ("11:00am", ("11:00", "am")),
        ("10:30pm", ("10:30", "pm")),
        ("10:30am", ("10:30", "am")),
        ("12:00pm", ("12:00", "pm")),
        ("12:00am", ("12:00", "am")),
        ("6pm", ("6", "pm")),
        ("6am", ("6", "am")),
        ("hello", ("hello", None)),
        ("xyz", ("xyz", None)),
        ("14:30", ("14:30", None)),
        ("00:00", ("00:00", None)),
        ("5   pm", ("5", "pm")),
        ("10    am", ("10", "am")),
        ("12:15 pm", ("12:15", "pm")),
        ("12:15 am", ("12:15", "am")),
        ("7:00pm", ("7:00", "pm")),
        ("8  pm", ("8", "pm")),
        ("9   am", ("9", "am")),

        # --- suffix not at end ---
        ("6am-11", ("6am-11", None)),
    ]

    for i, (inp, exp) in enumerate(cases):
        out = utils.extract_global_suffix(inp)
        check(f"suffix {i}", out == exp)
def test_is_open_during_window():

    open_features = {
        "Monday_openHours": [(17, 24), (0, 6)],
        "Tuesday_openHours": [(10, 18)],
    }

    cases = [
        ((20, 2), True),
        ((23, 1), True),
        ((5, 6), True),
        ((7, 9), False),
        ((10, 12), True),
        ((17, 23), True),
        ((0, 1), True),
        ((12, 13), True),
        ((6, 7), False),
        ((18, 20), False),

        ((22, 23), True),
        ((1, 3), True),
        ((3, 5), True),
        ((8, 9), False),
        ((9, 11), True),

        ((11, 13), True),
        ((13, 15), True),
        ((15, 17), True),

        ((17, 18), True),
        ((18, 19), False),

        # --- 30 more cases ---
        ((0, 2), True),
        ((2, 4), True),
        ((4, 6), True),
        ((6, 8), False),
        ((8, 10), False),
        ((10, 11), True),
        ((11, 12), True),
        ((12, 14), True),
        ((14, 16), True),
        ((16, 18), True),
        ((17, 19), True),
        ((19, 21), False),
        ((21, 23), True),
        ((23, 24), True),
        ((0, 0.5), True),
        ((5.5, 6), True),
        ((6, 6.5), False),
        ((17, 17.5), True),
        ((23.5, 24), True),
        ((1, 2), True),
        ((3, 4), True),
        ((5, 5.5), True),
        ((10, 10.5), True),
        ((12, 12.5), True),
        ((15, 15.5), True),
        ((17.5, 18), True),
        ((18, 18.5), False),
        ((9.5, 10.5), True),
        ((16.5, 17.5), True),
        ((7.5, 8.5), False),
    ]

    for i, (query, expected) in enumerate(cases):
        res = utils.is_open_during_window(open_features, [query])
        check(f"open_check {i}", res == expected)

def test_parse_time_window():

    cases = [
        ("20:00-06:00", [(20, 24), (0, 6)]),
        ("10:00-14:00", [(10, 14)]),
        ("00:00-01:00", [(0, 1)]),
        ("23:00-02:00", [(23, 24), (0, 2)]),
        ("05:00-06:00", [(5, 6)]),
        ("18:30-20:00", [(18.5, 20)]),
        ("21:15-22:45", [(21.25, 22.75)]),
        ("12:00-13:00", [(12, 13)]),
        ("14:00-15:00", [(14, 15)]),
        ("16:00-17:00", [(16, 17)]),
        ("17:00-18:00", [(17, 18)]),
        ("19:00-20:00", [(19, 20)]),
        ("07:00-08:00", [(7, 8)]),
        ("08:00-09:00", [(8, 9)]),
        ("09:00-10:00", [(9, 10)]),
        ("11:00-12:00", [(11, 12)]),
        ("13:00-14:00", [(13, 14)]),
        ("15:00-16:00", [(15, 16)]),
        ("22:00-23:00", [(22, 23)]),
        ("01:00-03:00", [(1, 3)]),

        # --- 30 more cases ---
        ("00:00-12:00", [(0, 12)]),
        ("12:00-24:00", [(12, 24)]),
        ("06:00-18:00", [(6, 18)]),
        ("18:00-06:00", [(18, 24), (0, 6)]),
        ("22:00-06:00", [(22, 24), (0, 6)]),
        ("08:30-17:30", [(8.5, 17.5)]),
        ("09:15-18:45", [(9.25, 18.75)]),
        ("00:30-01:30", [(0.5, 1.5)]),
        ("23:45-00:15", [(23.75, 24), (0, 0.25)]),
        ("03:00-15:00", [(3, 15)]),
        ("04:00-16:00", [(4, 16)]),
        ("05:30-14:30", [(5.5, 14.5)]),
        ("07:45-19:45", [(7.75, 19.75)]),
        ("10:10-22:10", [(10 + 1/6, 22 + 1/6)]),
        ("11:59-23:59", [(11 + 59/60, 23 + 59/60)]),
        ("02:00-14:00", [(2, 14)]),
        ("00:00-00:00", [(0, 0)]),
        ("12:00-12:00", [(12, 12)]),
        ("08:00-20:00", [(8, 20)]),
        ("20:00-08:00", [(20, 24), (0, 8)]),
        ("17:30-18:30", [(17.5, 18.5)]),
        ("06:15-07:15", [(6.25, 7.25)]),
        ("13:45-14:45", [(13.75, 14.75)]),
        ("21:00-03:00", [(21, 24), (0, 3)]),
        ("19:30-07:30", [(19.5, 24), (0, 7.5)]),
        ("16:45-17:45", [(16.75, 17.75)]),
        ("00:15-00:45", [(0.25, 0.75)]),
        ("23:30-23:59", [(23.5, 23 + 59/60)]),
        ("01:30-02:30", [(1.5, 2.5)]),

        # --- spaces around dash ---
        ("10:00 - 14:00", [(10, 14)]),
        ("20:00 - 06:00", [(20, 24), (0, 6)]),
        (" 10:00 - 14:00 ", [(10, 14)]),
        ("08:30 - 17:30", [(8.5, 17.5)]),
        ("22:00  -  06:00", [(22, 24), (0, 6)]),
    ]

    for i, (inp, exp) in enumerate(cases):
        out = utils.parse_time_window(inp)
        check(f"parse_time_window {i}", out == exp)

def test_get_suffix():

    cases = [
        # single suffix → return it
        ("5:30am", "am"),
        ("7:45pm", "pm"),
        ("9am", "am"),
        ("11pm", "pm"),
        ("5:30", None),
        ("14:00", None),
        ("", None),

        # both suffixes present → None (no single global)
        ("4am-5pm", None),
        ("5pm-6am", None),
        ("10am-10pm", None),
        ("12pm-12am", None),
        ("9:00am-5:00pm", None),
        ("6pm-2am", None),
        ("3 am-5 pm", None),

        # same suffix both sides → return it
        ("9am-11am", "am"),
        ("5pm-10pm", "pm"),
        ("4:00pm-8:00pm", "pm"),
        ("10:00am-11:30am", "am"),

        # no suffix at all
        ("10:00-14:00", None),
        ("no suffix here", None),
    ]

    for i, (inp, exp) in enumerate(cases):
        out = utils.get_suffix(inp)
        check(f"get_suffix {i}", out == exp, expected=exp, got=out)

def test_normalize_dashes():

    cases = [
        ("9am–5pm", "9am-5pm"),       # en-dash
        ("10am—6pm", "10am-6pm"),     # em-dash
        ("11am-7pm", "11am-7pm"),     # regular hyphen (no change)
        ("2pm−10pm", "2pm-10pm"),     # minus sign
        ("8am–5pm—9pm", "8am-5pm-9pm"),  # multiple
        ("", ""),
        ("no dash here", "no dash here"),
        ("––—", "---"),               # all dashes
        ("5:30–7:30 pm", "5:30-7:30 pm"),
        ("open–close", "open-close"),
    ]

    for i, (inp, exp) in enumerate(cases):
        out = utils.normalize_dashes(inp)
        check(f"normalize_dashes {i}", out == exp, expected=exp, got=out)

if __name__ == "__main__":
    print("Running full 20x-per-function test suite...\n")

    
    test_normalize_time()
    test_normalize_interval()
    test_parse_time_window()
    test_parse_interval()
    test_safe_json_load()
    test_haversine()
    test_extract_open_close()
    test_popular_times()
    test_get_suffix()
    test_normalize_dashes()

    print("\nALL TESTS PASSED ✅")