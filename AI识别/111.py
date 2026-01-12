import numpy as np
import matplotlib.pyplot as plt

def plot_resistance_curve():
    # ------------------------------
    # 1. 定义参数 (可根据需要修改)
    # ------------------------------
    Ft = 50       # 设置重量 (kg)，假设为50kg作为示例
    Lp = 100      # 预设伸长量 (cm)，假设为100cm作为示例
    a_values = [0, 0.5, 1, 2, 5, 10]  # 曲度参数 a 的不同取值
    
    # 定义 x 轴数据 (实时伸长量 Delta Lr)，从 0 到 Lp
    Lr = np.linspace(0, Lp, 500)

    # ------------------------------
    # 2. 定义阻力计算函数
    # ------------------------------
    def calculate_Fr(Lr, Ft, Lp, a):
        # 处理 a=0 的特殊情况 (使用极限：线性关系)
        if a == 0:
            return Ft * (Lr / Lp)
        else:
            # 你的公式: Fr = Ft * (e^(a * Lr/Lp) - 1) / (e^a - 1)
            term1 = np.exp(a * (Lr / Lp)) - 1
            term2 = np.exp(a) - 1
            return Ft * (term1 / term2)

    # ------------------------------
    # 3. 绘图设置
    # ------------------------------
    plt.figure(figsize=(10, 6), dpi=120) # 设置画布大小和分辨率

    # 颜色映射，为了区分不同曲线
    colors = ['black', 'blue', 'green', '#D4AC0D', 'orange', 'red']
    
    # 循环绘制每一条曲线
    for i, a in enumerate(a_values):
        Fr = calculate_Fr(Lr, Ft, Lp, a)
        label_text = f'a = {a}'
        if a == 0: label_text += ' (Linear)'
        plt.plot(Lr, Fr, label=label_text, color=colors[i], linewidth=2)

    # ------------------------------
    # 4. 图表美化与标注
    # ------------------------------
    plt.title(f'Resistance Curve Simulation: $F_r$ vs $\Delta L_r$ (Set Weight: {Ft}kg)', fontsize=14)
    plt.xlabel('Real-time Elongation $\Delta L_r$ (cm)', fontsize=12)
    plt.ylabel('Real-time Resistance $F_r$ (kg)', fontsize=12)
    
    # 设置坐标轴范围
    plt.xlim(0, Lp)
    plt.ylim(0, Ft * 1.05) # 稍微留一点顶部空间
    
    # 添加网格
    plt.grid(True, which='both', linestyle='--', alpha=0.6)
    
    # 标记关键点 (Lp, Ft)
    plt.plot(Lp, Ft, 'ko', markersize=5)
    plt.text(Lp, Ft, f'  Target ({Lp}cm, {Ft}kg)', verticalalignment='bottom')

    # 显示图例
    plt.legend(title="Curvature Param (a)", loc='upper left')

    # 显示图像
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_resistance_curve()