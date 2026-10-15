import asyncio
import unittest
from types import SimpleNamespace

from langgraph.types import Command

from app.services.ai_service import stream_chat_events


class FakeGraph:
    def __init__(
        self,
        events,
        *,
        snapshot_values=None,
        interrupts=None,
        snapshot_after_stream=None,
    ):
        self.events = events
        self.snapshot_values = snapshot_values or {}
        self.interrupts = interrupts or []
        self.snapshot_after_stream = snapshot_after_stream
        self.stream_completed = False
        self.input_payload = None

    async def aget_state(self, config):
        if self.stream_completed and self.snapshot_after_stream is not None:
            return self.snapshot_after_stream
        return SimpleNamespace(values=self.snapshot_values, tasks=[SimpleNamespace(interrupts=self.interrupts)])

    async def astream_events(self, *args, **kwargs):
        self.input_payload = args[0]
        for event in self.events:
            yield event
        self.stream_completed = True


class StreamChatEventsTests(unittest.TestCase):
    def test_stream_chat_events_emits_status_tool_and_token_events(self):
        async def run_test():
            graph = FakeGraph(
                [
                    {"event": "on_tool_start", "name": "list_open_labs"},
                    {
                        "event": "on_tool_end",
                        "name": "list_open_labs",
                        "data": {"output": "content='raw tool response' name='list_open_labs'"},
                    },
                    {
                        "event": "on_chat_model_stream",
                        "metadata": {"langgraph_node": "agent"},
                        "data": {"chunk": {"content": "你好，实验室开放情况如下："}},
                    },
                ]
            )
            current_user = SimpleNamespace(id=1)
            data = SimpleNamespace(message="查看开放实验室", thread_id=None)

            events = []
            async for event in stream_chat_events(graph, current_user, data):
                events.append(event)

            self.assertEqual(events[0]["type"], "meta")
            self.assertEqual(events[1]["type"], "status")
            self.assertEqual(events[2]["type"], "tool_start")
            self.assertEqual(events[3]["type"], "tool_end")
            self.assertNotIn("preview", events[3])
            self.assertNotIn("raw tool response", str(events))
            self.assertEqual(events[4]["type"], "token")
            self.assertTrue(events[-1]["type"] in {"done", "error"})

        async def run_new_draft_test():
            draft = {
                "lab_name": "计算机基础实验室",
                "location": "实验楼 A301",
                "date": "2026-10-17",
                "start_time": "09:00",
                "end_time": "10:00",
            }
            graph = FakeGraph(
                [
                    {"event": "on_tool_start", "name": "prepare_reservation"},
                    {"event": "on_tool_end", "name": "prepare_reservation", "data": {"output": "private draft payload"}},
                ],
                snapshot_after_stream=SimpleNamespace(
                    values={"pending_reservation": draft},
                    tasks=[SimpleNamespace(interrupts=[SimpleNamespace(value={"draft": draft})])],
                ),
            )
            events = []
            async for event in stream_chat_events(
                graph,
                SimpleNamespace(id=1),
                SimpleNamespace(message="预约实验室", thread_id=None),
            ):
                events.append(event)

            confirmation = next(event for event in events if event["type"] == "confirmation")
            self.assertIn("计算机基础实验室", confirmation["message"])
            self.assertTrue(confirmation["pending_confirmation"])
            self.assertNotIn("private draft payload", str(events))
            self.assertEqual(events[-1]["type"], "done")

        async def run_confirmation_test():
            graph = FakeGraph(
                [],
                snapshot_values={"pending_reservation": {"lab_name": "A301", "date": "2026-10-17"}},
                interrupts=[SimpleNamespace(value={"draft": {"lab_name": "A301", "date": "2026-10-17"}})],
                snapshot_after_stream=SimpleNamespace(
                    values={"final_answer": "预约已提交，当前状态为待管理员审核。"},
                    tasks=[],
                ),
            )
            current_user = SimpleNamespace(id=1)
            data = SimpleNamespace(message="确认预约", thread_id=None)
            events = []
            async for event in stream_chat_events(graph, current_user, data):
                events.append(event)
            self.assertEqual(events[0]["type"], "meta")
            self.assertEqual(events[1]["type"], "status")
            self.assertIsInstance(graph.input_payload, Command)
            self.assertEqual(graph.input_payload.resume, "确认预约")
            self.assertEqual(events[2]["type"], "token")
            self.assertEqual(events[2]["content"], "预约已提交，当前状态为待管理员审核。")
            self.assertEqual(events[3]["type"], "done")

        asyncio.run(run_test())
        asyncio.run(run_new_draft_test())
        asyncio.run(run_confirmation_test())


if __name__ == "__main__":
    unittest.main()
