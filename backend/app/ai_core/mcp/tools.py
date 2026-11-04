"""MCP: register all built-in read-only tools with strict input schemas."""
from app.ai_core.mcp.registry import (
    registry, student_tool, teacher_tool, parent_tool, school_admin_tool,
)

_EMPTY = {"type": "object", "properties": {}, "required": []}
_WITH_ID = {
    "type": "object",
    "properties": {"user_id": {"type": "string"}},
    "required": ["user_id"],
}

# Student tools
registry.register(student_tool("get_my_profile", "Get the current student's profile", _WITH_ID))
registry.register(student_tool("get_my_subjects", "List subjects for the current student", _EMPTY))
registry.register(student_tool("get_my_timetable", "Get the current student's timetable", _EMPTY))
registry.register(student_tool("get_my_grades", "Get the current student's grades", _EMPTY))
registry.register(student_tool("get_my_attendance", "Get the current student's attendance", _EMPTY))
registry.register(student_tool("get_my_homework", "Get the current student's homework", _EMPTY))

# Teacher tools
registry.register(teacher_tool("get_my_classes", "List classes assigned to the current teacher", _EMPTY))
registry.register(teacher_tool("get_class_students", "List students in a class", {
    "type": "object", "properties": {"class_id": {"type": "string"}}, "required": ["class_id"]}))
registry.register(teacher_tool("get_class_timetable", "Get timetable for a class", {
    "type": "object", "properties": {"class_id": {"type": "string"}}, "required": ["class_id"]}))
registry.register(teacher_tool("get_student_learning_progress", "Get a student's learning progress", {
    "type": "object", "properties": {"student_id": {"type": "string"}}, "required": ["student_id"]}))
registry.register(teacher_tool("get_assignment_submissions", "List submissions for an assignment", {
    "type": "object", "properties": {"assignment_id": {"type": "string"}}, "required": ["assignment_id"]}))

# Parent tools
registry.register(parent_tool("get_linked_children", "List the current parent's linked children", _EMPTY))
registry.register(parent_tool("get_child_grades", "Get a child's grades", {
    "type": "object", "properties": {"child_id": {"type": "string"}}, "required": ["child_id"]}))
registry.register(parent_tool("get_child_attendance", "Get a child's attendance", {
    "type": "object", "properties": {"child_id": {"type": "string"}}, "required": ["child_id"]}))
registry.register(parent_tool("get_child_timetable", "Get a child's timetable", {
    "type": "object", "properties": {"child_id": {"type": "string"}}, "required": ["child_id"]}))

# School Admin tools
registry.register(school_admin_tool("get_school_statistics", "Get school-level statistics", _EMPTY))
registry.register(school_admin_tool("get_school_classes", "List school classes", _EMPTY))
registry.register(school_admin_tool("get_school_teachers", "List school teachers", _EMPTY))
registry.register(school_admin_tool("get_school_students", "List school students", _EMPTY))

__all__ = ["registry"]
