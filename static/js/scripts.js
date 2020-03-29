function main() {
	window.location.href = 'http://127.0.0.1:8000/main';
}
function logout() {
	window.location.href = 'http://127.0.0.1:8000/exit';
}
function settings() {
	window.location.href = 'http://127.0.0.1:8000/settings';
}
function restore() {
	window.location.href = 'http://127.0.0.1:8000/restore';
}
function admin() {
	window.location.href = 'http://127.0.0.1:8000/admin/main'
}
function new_competition() {
	window.location.href = 'http://127.0.0.1:8000/admin/new_competition'
}
function new_task(competition_id) {
	window.location.href = 'http://127.0.0.1:8000/admin/new_task?competition_id=' + competition_id
}
function solutions(competition_id) {
	window.location.href = 'http://127.0.0.1:8000/admin/solutions?competition_id=' + competition_id
}
function delete_solution(competition_id) {
	let del = confirm("Точно удаляем?");
	if (del) window.location.href = 'http://127.0.0.1:8000/admin/delete_competition?competition_id=' + competition_id
}
function delete_task(task_id) {
	let del = confirm("Точно удаляем?");
	if (del) window.location.href = 'http://127.0.0.1:8000/admin/delete_task?task_id=' + task_id
}
function remove_tests(task_id) {
	let del = confirm("Точно удаляем?");
	if (del) window.location.href = 'http://127.0.0.1:8000/admin/remove_tests?task_id=' + task_id
}