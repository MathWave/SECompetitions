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
function new_task(competition_name) {
	window.location.href = 'http://127.0.0.1:8000/admin/new_task/' + competition_name
}
function solutions(competition_name) {
	window.location.href = 'http://127.0.0.1:8000/admin/solutions/' + competition_name
}
function delete_solution(competition_name) {
	let del = confirm("Точно удаляем?");
	if (del) window.location.href = 'http://127.0.0.1:8000/admin/delete_competition/' + competition_name
}
function delete_task(competition_name, task_name) {
	let del = confirm("Точно удаляем?");
	if (del) window.location.href = 'http://127.0.0.1:8000/admin/delete_task/' + competition_name + '/' + task_name
}
function remove_tests(competition_name, task_name) {
	let del = confirm("Точно удаляем?");
	if (del) window.location.href = 'http://127.0.0.1:8000/admin/remove_tests/' + competition_name + '/' + task_name
}