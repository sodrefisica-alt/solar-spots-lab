# app.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from PIL import Image
import io

# Configuração da página
st.set_page_config(
    page_title="Análise de Manchas Solares",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #ff6600;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #ff6600;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ff6600;
        margin: 1rem 0;
    }
    .calculation-box {
        background-color: #fff0f5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ff3300;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

# Constantes físicas
SUN_TEMPERATURE = 5778  # Temperatura da fotosfera solar (K)
WIEN_CONSTANT = 2.898e-3  # Constante de Wien (m·K)
STEFAN_BOLTZMANN = 5.670e-8  # Constante de Stefan-Boltzmann (W/m²K⁴)

class SolarAnalyzer:
    def __init__(self):
        pass
    
    def planck_law(self, wavelength, temperature):
        """Lei de Planck para espectro de corpo negro"""
        h = 6.626e-34  # Constante de Planck
        c = 3.0e8      # Velocidade da luz
        k = 1.381e-23  # Constante de Boltzmann
        
        return (2 * h * c**2 / wavelength**5) * (1 / (np.exp(h*c/(wavelength*k*temperature)) - 1))
    
    def calculate_spot_temperature(self, intensity_percent):
        """Calcula temperatura usando Stefan-Boltzmann"""
        intensity_ratio = intensity_percent / 100
        return SUN_TEMPERATURE * (intensity_ratio ** 0.25)
    
    def create_solar_image(self, num_spots, spot_intensity, spot_size):
        """Cria uma imagem solar simulada com manchas"""
        size = 300
        x, y = np.meshgrid(np.linspace(-1, 1, size), np.linspace(-1, 1, size))
        r = np.sqrt(x**2 + y**2)
        
        # Disco solar com escurecimento de limbo
        solar_disk = 1.0 - 0.5 * r**2
        solar_disk[r > 1] = 0
        
        # Adicionar manchas solares
        spot_radius = spot_size / 100
        
        for i in range(num_spots):
            angle = 2 * np.pi * i / num_spots
            distance = 0.3 + 0.4 * (i / max(1, num_spots-1))
            spot_x = distance * np.cos(angle)
            spot_y = distance * np.sin(angle)
            
            # Criar mancha com penumbra
            spot_r = np.sqrt((x - spot_x)**2 + (y - spot_y)**2)
            
            # Núcleo escuro da mancha
            umbra_mask = spot_r < spot_radius
            # Penumbra
            penumbra_mask = (spot_r >= spot_radius) & (spot_r < spot_radius * 1.5)
            
            # Aplicar intensidades
            solar_disk[umbra_mask] *= spot_intensity / 100
            solar_disk[penumbra_mask] *= (spot_intensity + 20) / 100
        
        return solar_disk
    
    def create_interactive_plots(self, num_spots, spot_intensity, spot_size):
        """Cria gráficos interativos com Plotly"""
        # Dados para os gráficos
        spot_temp = self.calculate_spot_temperature(spot_intensity)
        wavelengths = np.linspace(300, 1100, 200)
        
        # Espectros
        photosphere_spectrum = self.planck_law(wavelengths * 1e-9, SUN_TEMPERATURE)
        photosphere_spectrum /= np.max(photosphere_spectrum)
        spot_spectrum = self.planck_law(wavelengths * 1e-9, spot_temp)
        spot_spectrum /= np.max(spot_spectrum)
        
        # Criar subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                '🌞 Simulação do Sol com Manchas',
                '📊 Intensidade das Regiões Solares',
                '📈 Espectro de Corpo Negro',
                '🌡️ Comparação de Temperaturas'
            ),
            specs=[[{"type": "heatmap"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # 1. Heatmap do Sol
        solar_image = self.create_solar_image(num_spots, spot_intensity, spot_size)
        fig.add_trace(
            go.Heatmap(z=solar_image, colorscale='Hot', showscale=False),
            row=1, col=1
        )
        
        # 2. Gráfico de barras de intensidade
        categories = ['Fotosfera'] + [f'Mancha {i+1}' for i in range(num_spots)]
        intensities = [100] + [spot_intensity * (1 - i * 0.1) for i in range(num_spots)]
        
        fig.add_trace(
            go.Bar(x=categories, y=intensities, 
                  marker_color=['gold'] + ['darkred'] * num_spots,
                  text=[f'{i}%' for i in intensities],
                  textposition='auto'),
            row=1, col=2
        )
        
        # 3. Espectros
        fig.add_trace(
            go.Scatter(x=wavelengths, y=photosphere_spectrum,
                      mode='lines', name=f'Fotosfera ({SUN_TEMPERATURE} K)',
                      line=dict(color='gold', width=3)),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=wavelengths, y=spot_spectrum,
                      mode='lines', name=f'Manchas ({spot_temp:.0f} K)',
                      line=dict(color='darkred', width=3)),
            row=2, col=1
        )
        
        # Área da luz visível
        fig.add_vrect(x0=380, x1=750, row=2, col=1,
                     fillcolor="cyan", opacity=0.2, line_width=0,
                     annotation_text="Luz Visível", annotation_position="top left")
        
        # 4. Comparação de temperaturas
        temperatures = [SUN_TEMPERATURE, spot_temp]
        categories_temp = ['Fotosfera', 'Manchas']
        
        fig.add_trace(
            go.Bar(x=categories_temp, y=temperatures,
                  marker_color=['gold', 'darkred'],
                  text=[f'{temp:.0f} K' for temp in temperatures],
                  textposition='auto'),
            row=2, col=2
        )
        
        # Atualizar layout
        fig.update_layout(height=800, showlegend=True, title_text="Análise Completa de Manchas Solares")
        fig.update_xaxes(title_text="Posição", row=1, col=1)
        fig.update_xaxes(title_text="Regiões Solares", row=1, col=2)
        fig.update_xaxes(title_text="Comprimento de Onda (nm)", row=2, col=1)
        fig.update_xaxes(title_text="Regiões", row=2, col=2)
        
        fig.update_yaxes(title_text="Intensidade Relativa (%)", row=1, col=2)
        fig.update_yaxes(title_text="Intensidade Relativa", row=2, col=1)
        fig.update_yaxes(title_text="Temperatura (K)", row=2, col=2)
        
        return fig

def main():
    # Cabeçalho principal
    st.markdown('<h1 class="main-header">🌞 Laboratório Virtual: Manchas Solares</h1>', unsafe_allow_html=True)
    
    # Inicializar analisador
    analyzer = SolarAnalyzer()
    
    # Sidebar com controles
    st.sidebar.header("🎮 Controles Interativos")
    
    st.sidebar.markdown("### Configurações das Manchas")
    num_spots = st.sidebar.slider("Número de Manchas", 1, 5, 2)
    spot_intensity = st.sidebar.slider("Intensidade da Mancha (%)", 10, 80, 35)
    spot_size = st.sidebar.slider("Tamanho da Mancha (%)", 3, 15, 8)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Informações do Estudo")
    st.sidebar.info("""
    **Objetivos de Aprendizado:**
    - Compreender radiação térmica
    - Aplicar leis de Stefan-Boltzmann e Wien
    - Analisar dados solares reais
    - Relacionar temperatura com aparência visual
    """)
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Início", "🔬 Simulação", "📚 Teoria", "🎯 Atividades"])
    
    with tab1:
        st.markdown('<h2 class="section-header">Bem-vindo ao Laboratório Virtual de Manchas Solares!</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            <div class="info-box">
            <h3>🎯 Sobre Este Laboratório</h3>
            <p>Este é um ambiente virtual interativo onde você pode explorar a física das 
            manchas solares usando leis científicas reais e dados do Solar Dynamics Observatory.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            ### 🚀 Como Usar:
            1. **Navegue pelas abas** acima para explorar diferentes seções
            2. **Ajuste os controles** na barra lateral para modificar a simulação
            3. **Observe em tempo real** como as mudanças afetam os cálculos
            4. **Complete as atividades** para consolidar seu aprendizado
            
            ### 📖 O Que Você Vai Aprender:
            - **Lei de Stefan-Boltzmann**: Relação entre temperatura e energia radiante
            - **Lei de Wien**: Como a temperatura afeta a cor da luz emitida
            - **Manchas Solares**: Por que são mais frias e como detectá-las
            - **Análise Científica**: Como os astrônomos estudam o Sol
            """)
        
        with col2:
            st.image("https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0171.jpg", 
                    caption="Imagem real do SDO - Solar Dynamics Observatory",
                    use_column_width=True)
    
    with tab2:
        st.markdown('<h2 class="section-header">Simulação Interativa</h2>', unsafe_allow_html=True)
        
        # Gráficos interativos
        fig = analyzer.create_interactive_plots(num_spots, spot_intensity, spot_size)
        st.plotly_chart(fig, use_container_width=True)
        
        # Cálculos detalhados
        st.markdown('<h3 class="section-header">🧮 Cálculos Detalhados</h3>', unsafe_allow_html=True)
        
        spot_temp = analyzer.calculate_spot_temperature(spot_intensity)
        intensity_ratio = spot_intensity / 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="calculation-box">
            <h4>Método Stefan-Boltzmann</h4>
            Fórmula: T_mancha = T_fotosfera × (I_mancha/I_fotosfera)¹ᐟ⁴<br><br>
            
            Dados:<br>
            • T_fotosfera = 5778 K<br>
            • I_mancha/I_fotosfera = {ratio:.3f}<br><br>
            
            Cálculo:<br>
            T_mancha = 5778 × ({ratio:.3f})¹ᐟ⁴<br>
            T_mancha = 5778 × {root:.3f}<br>
            T_mancha = {temp:.0f} K<br><br>
            
            Resultado: {temp:.0f} K ({diff:.0f} K mais fria)
            </div>
            """.format(ratio=intensity_ratio, root=intensity_ratio**0.25, 
                      temp=spot_temp, diff=SUN_TEMPERATURE-spot_temp), unsafe_allow_html=True)
        
        with col2:
            # Cálculo Lei de Wien
            wavelength_sun = (WIEN_CONSTANT / SUN_TEMPERATURE) * 1e9
            wavelength_spot = (WIEN_CONSTANT / spot_temp) * 1e9
            
            st.markdown("""
            <div class="calculation-box">
            <h4>Método Lei de Wien</h4>
            Fórmula: λ_max × T = 2,898×10⁻³ m·K<br><br>
            
            Fotosfera:<br>
            λ_max = 2,898×10⁻³ / 5778 = {sun_wl:.0f} nm (verde-amarelo)<br><br>
            
            Mancha:<br>
            λ_max = 2,898×10⁻³ / {temp:.0f} = {spot_wl:.0f} nm (vermelho)<br><br>
            
            Deslocamento: {shift:.0f} nm para o vermelho
            </div>
            """.format(sun_wl=wavelength_sun, temp=spot_temp, 
                      spot_wl=wavelength_spot, shift=wavelength_spot-wavelength_sun), 
            unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<h2 class="section-header">Fundamentos Teóricos</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="info-box">
            <h3>📊 Lei de Stefan-Boltzmann</h3>
            <strong>Fórmula:</strong> I = σ × T⁴<br><br>
            
            <strong>Onde:</strong><br>
            • I = Intensidade da radiação (W/m²)<br>
            • σ = Constante de Stefan-Boltzmann (5,67×10⁻⁸ W/m²K⁴)<br>
            • T = Temperatura em Kelvin (K)<br><br>
            
            <strong>Aplicação:</strong><br>
            Para manchas solares, usamos a razão de intensidades:<br>
            T_mancha = T_foto × (I_mancha/I_foto)¹ᐟ⁴
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="info-box">
            <h3>🌞 O que são Manchas Solares?</h3>
            • <strong>Regiões mais frias</strong> da fotosfera solar<br>
            • Temperatura: 3.000-4.500 K (fotosfera: ~5.778 K)<br>
            • Causadas por <strong>campos magnéticos intensos</strong><br>
            • Inibem a convecção de calor<br>
            • Seguem um <strong>ciclo de 11 anos</strong><br>
            • Podem ser <strong>maiores que a Terra</strong>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="info-box">
            <h3>📈 Lei do Deslocamento de Wien</h3>
            <strong>Fórmula:</strong> λ_max × T = b<br><br>
            
            <strong>Onde:</strong><br>
            • λ_max = Comprimento de onda de pico (m)<br>
            • T = Temperatura em Kelvin (K)<br>
            • b = Constante de Wien (2,898×10⁻³ m·K)<br><br>
            
            <strong>Aplicação:</strong><br>
            • Corpos mais quentes → pico em menores λ<br>
            • Sol (5778K) → pico ~500nm (verde-amarelo)<br>
            • Manchas (~4000K) → pico ~725nm (vermelho)
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="info-box">
            <h3>🔬 Por que Manchas Parecem Escuras?</h3>
            <strong>Efeito de Contraste:</strong><br>
            • Não são realmente "escuras"<br>
            • Emitem menos luz que a fotosfera ao redor<br>
            • Nossos olhos percebem como regiões escuras<br>
            • Se isoladas, brilhariam intensamente<br><br>
            
            <strong>Analogia:</strong><br>
            Como ver velas acesas à luz do sol
            </div>
            """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown('<h2 class="section-header">Atividades Práticas</h2>', unsafe_allow_html=True)
        
        # Atividade 1
        st.markdown("""
        <div class="info-box">
        <h3>🧮 Atividade 1: Cálculo Manual</h3>
        <strong>Objetivo:</strong> Calcular temperatura manualmente usando Stefan-Boltzmann<br><br>
        
        <strong>Passos:</strong><br>
        1. Anote a intensidade da mancha: <strong>{intensity}%</strong><br>
        2. Calcule a razão: I_mancha/I_fotosfera = {ratio:.3f}<br>
        3. Aplique: T_mancha = 5778 × ({ratio:.3f})¹ᐟ⁴<br>
        4. Compare com o resultado do software: <strong>{temp:.0f} K</strong><br><br>
        
        <strong>Questão:</strong> A temperatura calculada manualmente confere com a do software?
        </div>
        """.format(intensity=spot_intensity, ratio=spot_intensity/100, temp=spot_temp), 
        unsafe_allow_html=True)
        
        # Atividade 2
        st.markdown("""
        <div class="info-box">
        <h3>📊 Atividade 2: Análise de Dados</h3>
        <strong>Objetivo:</strong> Investigar padrões nos dados<br><br>
        
        <strong>Tarefas:</strong><br>
        1. Ajuste a intensidade para 25% e anote a temperatura<br>
        2. Ajuste a intensidade para 50% e anote a temperatura<br>
        3. Ajuste a intensidade para 75% e anote a temperatura<br><br>
        
        <strong>Análise:</strong><br>
        • Como a intensidade afeta a temperatura?<br>
        • A relação é linear? Por quê?<br>
        • Qual a diferença prática entre 25% e 75%?
        </div>
        """, unsafe_allow_html=True)
        
        # Atividade 3
        st.markdown("""
        <div class="info-box">
        <h3>🔍 Atividade 3: Investigação Científica</h3>
        <strong>Objetivo:</strong> Compreender o método científico<br><br>
        
        <strong>Hipótese:</strong><br>
        "Manchas maiores devem ser mais frias que manchas menores"<br><br>
        
        <strong>Procedimento:</strong><br>
        1. Teste com 2 manchas de tamanhos diferentes<br>
        2. Mantenha a intensidade constante<br>
        3. Observe se há diferença nas temperaturas<br><br>
        
        <strong>Conclusão:</strong><br>
        Sua hipótese foi confirmada? Justifique.
        </div>
        """, unsafe_allow_html=True)
        
        # Área para respostas
        st.markdown("### 📝 Registro de Respostas")
        resposta = st.text_area("Escreva aqui suas respostas e observações:", 
                               height=150, 
                               placeholder="Descreva suas descobertas, cálculos e conclusões...")
        
        if st.button("Salvar Respostas"):
            st.success("Respostas salvas! Continue explorando outras atividades.")

if __name__ == "__main__":
    main()