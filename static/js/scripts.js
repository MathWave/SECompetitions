function main() {
	window.location.href = 'http://192.168.1.8:8000/main'
}
function logout() {
	window.location.href = 'http://192.168.1.8:8000/exit'
}
function settings() {
	window.location.href = 'http://192.168.1.8:8000/settings'
}
function admin() {
	window.location.href = 'http://192.168.1.8:8000/admin/main'
}
function new_task(block_id) {
	window.location.href = 'http://192.168.1.8:8000/admin/new_task?block_id=' + block_id
}
function solutions(block_id) {
	window.location.href = 'http://192.168.1.8:8000/admin/solutions?block_id=' + block_id
}
function delete_solution(block_id) {
	let del = confirm("Точно удаляем?");
	if (del) window.location.href = 'http://192.168.1.8:8000/admin/delete_block?block_id=' + block_id
}
function delete_task(task_id) {
	let del = confirm("Точно удаляем?");
	if (del) window.location.href = 'http://192.168.1.8:8000/admin/delete_task?task_id=' + task_id
}
function remove_tests(task_id) {
	let del = confirm("Точно удаляем?");
	if (del) window.location.href = 'http://192.168.1.8:8000/admin/remove_tests?task_id=' + task_id
}