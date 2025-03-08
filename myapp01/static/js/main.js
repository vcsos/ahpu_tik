    // 初始化ECharts
    const likeChart = echarts.init(document.getElementById('likeChart'));
    likeChart.setOption({
        xAxis: {type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']},
        yAxis: {type: 'value'},
        series: [{
            data: [120, 200, 150, 80, 70, 110, 130],
            type: 'line',
            smooth: true,
            itemStyle: {color: '#2c7be5'}
        }]
    });
