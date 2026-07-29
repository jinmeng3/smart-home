import { onBeforeUnmount, shallowRef, type Ref } from 'vue'
import * as echarts from 'echarts/core'
import type { EChartsCoreOption, EChartsType } from 'echarts/core'
import { useVisibility } from './useVisibility'

export const useChart = (chartRef: Ref<HTMLDivElement | null>) => {
  const chartInstance = shallowRef<EChartsType | null>(null)
  const { isVisible } = useVisibility()
  let resizeTimer = 0

  const initChart = (option: EChartsCoreOption) => {
    if (!chartRef.value || chartInstance.value) {
      return
    }

    chartInstance.value = echarts.init(chartRef.value)
    chartInstance.value.setOption(option)
  }

  const updateChart = (option: EChartsCoreOption) => {
    chartInstance.value?.setOption(option)
  }

  const resizeChart = () => {
    if (!isVisible.value || !chartInstance.value) {
      return
    }

    window.clearTimeout(resizeTimer)
    resizeTimer = window.setTimeout(() => {
      chartInstance.value?.resize()
    }, 120)
  }

  const disposeChart = () => {
    window.clearTimeout(resizeTimer)
    chartInstance.value?.dispose()
    chartInstance.value = null
  }

  window.addEventListener('resize', resizeChart)

  onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeChart)
    disposeChart()
  })

  return {
    chartInstance,
    disposeChart,
    initChart,
    resizeChart,
    updateChart,
  }
}
