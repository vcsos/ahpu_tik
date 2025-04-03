// 登录注册界面大字浮动效果
window.onload = function () {
    var subtitle = document.getElementById('subtitle');
    var textToType = '欢迎使用短视频舆情分析可视化系统';
    var index = 0;
    var typingInterval;

    function type() {
        if (index < textToType.length) {
            subtitle.innerHTML += textToType.charAt(index);
            index++;
            typingInterval = setTimeout(type, 150);
        } else {
            clearTimeout(typingInterval);
        }
    }
    type();
};

        // 添加折叠菜单箭头动画
document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(button => {
    button.addEventListener('click', function() {
        const icon = this.querySelector('.toggle-icon');
        icon.classList.toggle('fa-angle-right');
        icon.classList.toggle('fa-angle-down');
    });
});