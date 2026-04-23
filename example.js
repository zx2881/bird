/**
 * 图谱数据源源
 */
export const data = [
    {
        id:1,
        name:'测试节点',
        categary:'1',
        symbolSize: 60
    },
    {
        id:2,
        name:'测试节点',
        categary:'1',
        symbolSize: 40
    },
    {
        id:3,
        name:'测试节点',
        categary:'2',
    },
    {
        id:4,
        name:'测试节点',
        categary:'',
    },
    {
        id:5,
        name:'测试节点测试节点',
        categary:'',
    },
    {
        id:6,
        name:'测试节点',
        categary:'2',
    },
    {
        id:7,
        name:'测试节点',
        categary:'',
    },
    {
        id:8,
        name:'测试节点',
        categary:'',
    },
    {
        id:9,
        name:'测试节点',
        categary:'',
    },
    {
        id:10,
        name:'测试节点',
        categary:'',测试节点
    }
];
//节点连线
let linkData = [
    {source: '2', target: '3', name: ''},
    {source: '3', target: '4', name: ''},
    {source: '3', target: '5', name: ''},
    {source: '5', target: '6', name: ''},
    {source: '5', target: '7', name: ''},
    {source: '5', target: '8', name: ''},
    {source: '9', target: '10', name: ''},
    {source: '10', target: '9', name: ''},
    {source: '1', target: '2' , name: ''},
    {source: '1', target: '10', name: ''}
    
]

/**
 * 模糊查询大类
 * @param {*} name 
 */
export const search = (name)=>{
    return new Promise((resolve,reject)=>{
        let result = {
            seriesData: [],
            linksData: []
        }
        let list = data.filter(item=>item.name.indexOf(name)>=0)
        if(list&&list.length>0){
            result.seriesData = list ||[];
        }else{
            result.seriesData = data ||[];
        }
        result.linksData = linkData ||[];
        if(list.length>0){
            resolve(result)
        }else{
            reject()
        }
    })
}


export const getAllData = ()=>{
    return new Promise((resolve,reject)=>{
        let result = {
            seriesData: [],
            linksData: []
        }
        result.seriesData = data||[];
        result.linksData = linkData ||[];
        if(data.length>0){
            resolve(result)
        }else{
            reject()
        }
    })
}

/**
 * 分类2
 */
export const categarys =  ["建设用地"]

<template>
  <div id="chart" class="chart"></div>
</template>
<script>
import { expendNodes } from "./mock";
var echarts = require("echarts/lib/echarts");
require("echarts/lib/chart/graph");
require("echarts/lib/component/tooltip");
require("echarts/lib/component/title");
export default {
  name: "Charts",
  props: {
    chartList: {
      type: Object,
      required: true,
    },
  },
  watch: {
    chartList: {
      handler(val) {
        this.formatData(val || [], true);
      },
    },
  },
  data() {
    return {
      myChart: "",
      seriesData: [],
      seriesLinks: [],
      categories:[],
      lastClickId: "",
      colors: ["#a3d2ca","#056676","#ea2c62","#16a596","#03c4a1","#f5a25d",
      "#8CD282","#32e0c4","#00FAE1","#f05454"], 
    };
  },
  methods: {
    /**
     * 节点点击事件
     */
    async nodeClick(params) {
      const index = this.seriesData.findIndex(
        (item) => item.id === params.data.id
      );
       console.log('点了节点:'+index+1,"clicked");
    },
    /**
     * 设置echarts配置项,重绘画布
     */
    initCharts() {
        const that = this;
      if (!this.myChart) {
        this.myChart = echarts.init(document.getElementById("chart"));
        this.myChart.on("click", (params) => {
          if (params.dataType === "node") {
            //判断点击的是图表的节点部分
            this.nodeClick(params);
          }
        });
      }
      // 指定图表的配置项和数据
      let option = {
        // 动画更新变化时间
        animationDurationUpdate: 500,
        animationEasingUpdate: "quinticInOut",
        tooltip: {
          show: false,
        },
        series: [
          {
            type: "graph",
            layout: "force",
            legendHoverLink: true, //是否启用图例 hover(悬停) 时的联动高亮。
            hoverAnimation: true, //是否开启鼠标悬停节点的显示动画
            focusNodeAdjacency: true,
            edgeLabel: {
              position: "middle", //边上的文字样式
              normal: {
                show: true,
                textStyle: {
                  fontSize: 12,
                },
                position: "middle",
                formatter: function (x) {
                  return x.data.name;
                },
              },
            },
            edgeSymbol: ["", "arrow"],
            force: {
                edgeLength: 15,
                repulsion: 200,
            },
            roam: true,
            draggable: true, //每个节点的拖拉
            itemStyle: {
              normal: {
                color: "#00FAE1",
                cursor: "pointer",
                //color:Math.floor(Math.random()*16777215).toString(16),
                 //color: ['#fc853e','#28cad8','#9564bf','#bd407e','#28cad8','#fc853e','#e5a214'],
                label: {
                 show: true,
                  position: [-10, -15],
                  textStyle: {
                    //标签的字体样式
                    color: "#fff", //字体颜色
                    fontStyle: "normal", //文字字体的风格 'normal'标准 'italic'斜体 'oblique' 倾斜
                    fontWeight: "bold", //'normal'标准'bold'粗的'bolder'更粗的'lighter'更细的或100 | 200 | 300 | 400...
                    fontFamily: "sans-serif", //文字的字体系列
                    fontSize: 12, //字体大小
                  },
                  
                },
                nodeStyle: {
                  brushType: "both",
                  borderColor: "rgba(255,215,0,0.4)",
                  borderWidth: 1,
                },
              },
              //鼠标放上去有阴影效果
              emphasis: {
                shadowColor: "#00FAE1",
                shadowOffsetX: 0,
                shadowOffsetY: 0,
                shadowBlur: 40,
                
              },
            },
            lineStyle: {
              width: 2,
            
            },
            label: {
               fontSize: 18,
            },
            symbolSize: 24, //节点大小
            links: this.seriesLinks,
            data: this.seriesData,
            categories:this.categories,
            cursor: "pointer",
          },
        ],
      };
      // 使用刚指定的配置项和数据显示图表。
      this.myChart.setOption(option);
    },
    /**
     * 格式化数据到表格需要的数据
     */
    formatData(list, reset = false) {
     const that =this;
      let nodes = list.seriesData;
      this.seriesData = [];
      this.seriesLinks = [];
      let colorIndex = 0;
      let data =[];
      let loadedCat=[];
      nodes.forEach((item,index)=>{
          if(item.categary && loadedCat.indexOf(item.categary) === -1){
              colorIndex = Math.floor((Math.random()*that.colors.length));
              loadedCat.push(item.categary);
              this.categories.push({name:item.categary});
          }
           item.itemStyle = {
              color: that.colors[colorIndex],
              borderColor: '#ffffff'
            }
        data.push(item);
      })
      this.seriesData.push(...data);
      this.seriesLinks.push(...list.linksData);
      this.initCharts();
    },
    
  },
  beforeDestroy() {},
};
</script>
<style scoped>
.chart {
  height: 100%;
}
</style>