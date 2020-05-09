function main() {
	window.location.href = 'http://mathwave.pythonanywhere.com/main'
}
function logout() {
	window.location.href = 'http://mathwave.pythonanywhere.com/exit'
}
function settings() {
	window.location.href = 'http://mathwave.pythonanywhere.com/settings'
}
function admin() {
	window.location.href = 'http://mathwave.pythonanywhere.com/admin/main'
}
function new_task(block_id) {
	window.location.href = 'http://mathwave.pythonanywhere.com/admin/new_task?block_id=' + block_id
}
function solutions(block_id) {
	window.location.href = 'http://mathwave.pythonanywhere.com/admin/solutions?block_id=' + block_id
}
function delete_solution(block_id) {
	let del = confirm("Точно удаляем?");
	if (del) window.location.href = 'http://mathwave.pythonanywhere.com/admin/delete_block?block_id=' + block_id
}
function delete_task(task_id) {
	let del = confirm("Точно удаляем?");
	if (del) window.location.href = 'http://mathwave.pythonanywhere.com/admin/delete_task?task_id=' + task_id
}
function remove_tests(task_id) {
	let del = confirm("Точно удаляем?");
	if (del) window.location.href = 'http://mathwave.pythonanywhere.com/admin/remove_tests?task_id=' + task_id
}