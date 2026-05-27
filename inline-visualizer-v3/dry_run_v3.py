import asyncio

import tool


def assert_contains(haystack: str, needle: str) -> None:
    if needle not in haystack:
        raise AssertionError(f"missing expected fragment: {needle}")


async def main() -> None:
    html = tool._build_html(
        security_level="strict",
        title="Dry Run Visualization",
        lang="zh-CN",
        chime=False,
    )

    assert_contains(html, 'data-iv-build="3.0.0"')
    assert_contains(html, "function scheduleTick(forceHide)")
    assert_contains(html, "var tickCache = null;")
    assert_contains(html, "var outerMo = null;")
    assert_contains(html, "clearInterval(pollTimer);")
    assert_contains(html, "function cleanupRuntimeWatchers()")
    assert "<meta http-equiv=\"Content-Security-Policy\"" in html
    assert "function playDoneSound()" not in html

    tools = tool.Tools()
    response, result_context = await tools.visualize(title="Dry Run Visualization")
    body = response.body.decode("utf-8")

    assert response.headers["content-disposition"] == "inline"
    assert_contains(body, 'data-iv-build="3.0.0"')
    assert_contains(result_context, "@@@VIZ-START")
    assert_contains(result_context, "@@@VIZ-END")

    print("v3 dry run passed")


if __name__ == "__main__":
    asyncio.run(main())
