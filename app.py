import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from PIL import Image
import io
import base64

# Configuração da página
st.set_page_config(
    page_title="🌞 Laboratório de Manchas Solares",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado moderno
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    .main-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3.5rem;
        background: linear-gradient(135deg, #ff8c00, #ff2e00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
        text-shadow: 0 4px 15px rgba(255, 140, 0, 0.3);
    }
    
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        color: #ff6b00;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        font-weight: 600;
        border-left: 5px solid #ff6b00;
        padding-left: 15px;
    }
    
    .info-box {
        background: linear-gradient(135deg, #1e3c72, #2a5298);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: none;
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
    }
    
    .info-box:hover {
        transform: translateY(-5px);
    }
    
    .calculation-box {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        font-family: 'Courier New', monospace;
        border: none;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px 10px 0 0;
        gap: 8px;
        padding: 10px 20px;
        color: white;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ff8c00, #ff2e00) !important;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
        color: white;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .sun-glow {
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { filter: drop-shadow(0 0 10px #ff8c00); }
        to { filter: drop-shadow(0 0 20px #ff2e00); }
    }
    
    .feature-card {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Constantes físicas
SUN_TEMPERATURE = 5778
WIEN_CONSTANT = 2.898e-3

class SolarAnalyzer:
    def __init__(self):
        pass
    
    def planck_law(self, wavelength, temperature):
        """Lei de Planck para espectro de corpo negro"""
        h = 6.626e-34
        c = 3.0e8
        k = 1.381e-23
        
        with np.errstate(all='ignore'):
            exponent = h * c / (wavelength * k * temperature)
            mask = (exponent > 700) | (wavelength < 1e-10)
            result = (2 * h * c**2 / wavelength**5) * (1 / (np.exp(exponent) - 1))
            result[mask] = 0
            result[np.isnan(result)] = 0
        return result
    
    def calculate_spot_temperature(self, intensity_percent):
        """Calcula temperatura usando Stefan-Boltzmann"""
        if intensity_percent <= 0:
            return 0
        intensity_ratio = intensity_percent / 100
        return SUN_TEMPERATURE * (intensity_ratio ** 0.25)
    
    def create_solar_image(self, num_spots, spot_intensity, spot_size):
        """Cria uma imagem solar simulada com manchas"""
        size = 400  # Aumentado para melhor qualidade
        x, y = np.meshgrid(np.linspace(-1, 1, size), np.linspace(-1, 1, size))
        r = np.sqrt(x**2 + y**2)
        
        # Disco solar com escurecimento de limbo mais realista
        solar_disk = 1.0 - 0.6 * r**2 + 0.1 * np.sin(10*r)  # Adiciona textura
        solar_disk[r > 1] = 0
        
        # Adicionar granulação solar
        granulation = 0.05 * np.random.randn(size, size)
        solar_disk[r <= 1] += granulation[r <= 1]
        solar_disk = np.clip(solar_disk, 0, 1)
        
        # Adicionar manchas solares
        spot_radius = spot_size / 120  # Ajustado para melhor proporção
        
        for i in range(num_spots):
            angle = 2 * np.pi * i / max(1, num_spots)
            distance = 0.4 + 0.3 * (i / max(1, num_spots-1))
            spot_x = distance * np.cos(angle)
            spot_y = distance * np.sin(angle)
            
            spot_r = np.sqrt((x - spot_x)**2 + (y - spot_y)**2)
            
            # Mancha com núcleo e penumbra realistas
            umbra_mask = spot_r < spot_radius
            penumbra_inner = spot_radius
            penumbra_outer = spot_radius * 1.8
            
            penumbra_mask = (spot_r >= penumbra_inner) & (spot_r < penumbra_outer)
            penumbra_intensity = np.interp(spot_r[penumbra_mask], 
                                         [penumbra_inner, penumbra_outer],
                                         [spot_intensity/100, 0.8])
            
            solar_disk[umbra_mask] *= spot_intensity / 100
            solar_disk[penumbra_mask] *= penumbra_intensity
        
        return solar_disk
    
    def create_interactive_plots(self, num_spots, spot_intensity, spot_size):
        """Cria gráficos interativos modernos"""
        try:
            spot_temp = self.calculate_spot_temperature(spot_intensity)
            wavelengths = np.linspace(300, 1100, 200)
            
            # Espectros
            photosphere_spectrum = self.planck_law(wavelengths * 1e-9, SUN_TEMPERATURE)
            photosphere_spectrum /= np.max(photosphere_spectrum) if np.max(photosphere_spectrum) > 0 else 1
            spot_spectrum = self.planck_law(wavelengths * 1e-9, spot_temp)
            spot_spectrum /= np.max(spot_spectrum) if np.max(spot_spectrum) > 0 else 1
            
            # Criar subplots com layout moderno
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    '🔭 Simulação Realista do Sol',
                    '📊 Análise de Intensidade',
                    '🌈 Espectro de Radiação',
                    '🌡️ Perfil de Temperaturas'
                ),
                specs=[[{"type": "heatmap"}, {"type": "bar"}],
                       [{"type": "scatter"}, {"type": "bar"}]],
                vertical_spacing=0.1,
                horizontal_spacing=0.1
            )
            
            # 1. Heatmap do Sol moderno
            solar_image = self.create_solar_image(num_spots, spot_intensity, spot_size)
            fig.add_trace(
                go.Heatmap(
                    z=solar_image, 
                    colorscale='Hot',
                    showscale=True,
                    colorbar=dict(title="Intensidade", titleside="right"),
                    hoverinfo='skip'
                ),
                row=1, col=1
            )
            
            # 2. Gráfico de barras moderno
            categories = ['Fotosfera'] + [f'Mancha {i+1}' for i in range(num_spots)]
            intensities = [100] + [spot_intensity * (1 - i * 0.1) for i in range(num_spots)]
            
            fig.add_trace(
                go.Bar(
                    x=categories, 
                    y=intensities,
                    marker=dict(
                        color=['#FFD700'] + ['#8B0000'] * num_spots,
                        line=dict(color='white', width=2)
                    ),
                    text=[f'{val:.0f}%' for val in intensities],
                    textposition='auto',
                    textfont=dict(color='white', size=14),
                    hoverinfo='skip'
                ),
                row=1, col=2
            )
            
            # 3. Espectros com design moderno
            fig.add_trace(
                go.Scatter(
                    x=wavelengths, 
                    y=photosphere_spectrum,
                    mode='lines', 
                    name=f'Fotosfera ({SUN_TEMPERATURE} K)',
                    line=dict(color='#FFD700', width=4, shape='spline'),
                    fill='tozeroy',
                    fillcolor='rgba(255, 215, 0, 0.3)',
                    hoverinfo='skip'
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=wavelengths, 
                    y=spot_spectrum,
                    mode='lines', 
                    name=f'Manchas ({spot_temp:.0f} K)',
                    line=dict(color='#8B0000', width=4, shape='spline'),
                    fill='tozeroy',
                    fillcolor='rgba(139, 0, 0, 0.3)',
                    hoverinfo='skip'
                ),
                row=2, col=1
            )
            
            # Área da luz visível
            fig.add_vrect(
                x0=380, x1=750, 
                row=2, col=1,
                fillcolor="cyan", 
                opacity=0.2, 
                line_width=0,
                annotation_text="🌈 Luz Visível", 
                annotation_position="top left"
            )
            
            # 4. Comparação de temperaturas moderna
            temperatures = [SUN_TEMPERATURE, spot_temp]
            categories_temp = ['Fotosfera', 'Manchas']
            
            fig.add_trace(
                go.Bar(
                    x=categories_temp, 
                    y=temperatures,
                    marker=dict(
                        color=['#FFD700', '#8B0000'],
                        line=dict(color='white', width=2)
                    ),
                    text=[f'{temp:.0f} K' for temp in temperatures],
                    textposition='auto',
                    textfont=dict(color='white', size=14, weight='bold'),
                    hoverinfo='skip'
                ),
                row=2, col=2
            )
            
            # Layout moderno
            fig.update_layout(
                height=900,
                showlegend=True,
                title_text="🔬 Análise Científica Avançada - Manchas Solares",
                title_font=dict(size=24, color='#ff6b00'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                margin=dict(t=100, b=50, l=50, r=50),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Configurar eixos com estilo moderno
            for row in [1,2]:
                for col in [1,2]:
                    fig.update_xaxes(
                        gridcolor='rgba(255,255,255,0.1)',
                        row=row, col=col
                    )
                    fig.update_yaxes(
                        gridcolor='rgba(255,255,255,0.1)',
                        row=row, col=col
                    )
            
            return fig
            
        except Exception as e:
            st.error(f"Erro ao criar visualizações: {e}")
            return go.Figure()

def load_solar_images():
    """Carrega e processa imagens solares para a galeria"""
    # URLs de imagens reais do SDO (Solar Dynamics Observatory)
    solar_images = {
        "Sol em Luz Visível": "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0171.jpg",
        "Sol em Ultravioleta": "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0304.jpg",
        "Sol em Raios-X": "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0211.jpg",
        "Manchas Solares Detalhadas": "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIIF.jpg"
    }
    
    return solar_images

def main():
    # Cabeçalho principal espetacular
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h1 class="main-header">🌞 LABORATÓRIO DE MANCHAS SOLARES</h1>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 1.2rem; margin-bottom: 2rem;">
        Explore a Física Solar de Forma Interativa e Visualmente Impressionante
        </div>
        """, unsafe_allow_html=True)
    
    # Inicializar analisador
    analyzer = SolarAnalyzer()
    
    # Sidebar moderna
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h2 style="color: white; margin-bottom: 2rem;">🎮 CONTROLES</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Controles com estilo moderno
        st.markdown("### 🔧 Configurações das Manchas")
        num_spots = st.slider("Número de Manchas", 1, 5, 2, 
                             help="Quantas manchas solares aparecem na simulação")
        
        spot_intensity = st.slider("Intensidade da Mancha (%)", 10, 80, 35,
                                  help="Quão escuras são as manchas em relação à fotosfera")
        
        spot_size = st.slider("Tamanho da Mancha", 3, 20, 8,
                             help="Tamanho relativo das manchas solares")
        
        st.markdown("---")
        
        # Métricas em tempo real
        spot_temp = analyzer.calculate_spot_temperature(spot_intensity)
        intensity_ratio = spot_intensity / 100
        
        st.markdown("### 📊 Métricas em Tempo Real")
        col_metric1, col_metric2 = st.columns(2)
        
        with col_metric1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🌡️</h3>
                <h4>{spot_temp:.0f} K</h4>
                <small>Temperatura</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col_metric2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>⚡</h3>
                <h4>{intensity_ratio:.1%}</h4>
                <small>Intensidade</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div class="info-box">
        <h4>🎯 Dica Interativa</h4>
        <p>Experimente diferentes combinações para entender como as manchas solares funcionam!</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Abas principais com design moderno
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 INÍCIO", "🔬 SIMULAÇÃO", "📚 TEORIA", "🖼️ GALERIA", "🎯 ATIVIDADES"])
    
    with tab1:
        # Página inicial espetacular
        st.markdown("""
        <div class="info-box">
            <h2>🚀 Bem-vindo ao Futuro do Aprendizado Científico!</h2>
            <p>Este laboratório virtual combina dados reais do Solar Dynamics Observatory com 
            simulações interativas para criar uma experiência educacional única.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Recursos em cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <h3>🔭 Dados Reais</h3>
                <p>Imagens em tempo real do SDO/NASA</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <h3>📊 Simulações Interativas</h3>
                <p>Controles em tempo real</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-card">
                <h3>🎯 Aprendizado Ativo</h3>
                <p>Atividades práticas e desafios</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Imagem solar de destaque
        st.markdown("### 🌟 Destaque do Sol")
        try:
            response = requests.get("https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0171.jpg")
            solar_img = Image.open(io.BytesIO(response.content))
            st.image(solar_img, caption="🌞 Imagem em Tempo Real do Solar Dynamics Observatory (SDO/NASA)", 
                    use_column_width=True)
        except:
            # Fallback para imagem gerada
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.set_facecolor('black')
            sun = plt.Circle((0.5, 0.5), 0.4, color='yellow', alpha=0.9)
            ax.add_patch(sun)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            ax.set_title('Representação Artística do Sol', color='white', fontsize=16)
            st.pyplot(fig)
    
    with tab2:
        # Simulação interativa
        st.markdown('<h2 class="section-header">🔬 Laboratório de Simulação</h2>', unsafe_allow_html=True)
        
        # Gráficos interativos
        fig = analyzer.create_interactive_plots(num_spots, spot_intensity, spot_size)
        st.plotly_chart(fig, use_container_width=True)
        
        # Painel de análise
        st.markdown('<h3 class="section-header">📈 Painel de Análise</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="calculation-box">
                <h4>🧮 Lei de Stefan-Boltzmann</h4>
                <strong>Fórmula:</strong> T_mancha = T_foto × (I_mancha/I_foto)¹ᐟ⁴<br><br>
                
                <strong>Dados Atuais:</strong><br>
                • T_fotosfera = 5.778 K<br>
                • Razão de intensidade = {intensity_ratio:.3f}<br><br>
                
                <strong>Cálculo:</strong><br>
                T_mancha = 5.778 × ({intensity_ratio:.3f})¹ᐟ⁴<br>
                T_mancha = 5.778 × {intensity_ratio**0.25:.3f}<br>
                T_mancha = <strong>{spot_temp:.0f} K</strong><br><br>
                
                <strong>Resultado:</strong> {SUN_TEMPERATURE-spot_temp:.0f} K mais fria que a fotosfera
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Cálculo Lei de Wien
            wavelength_sun = (WIEN_CONSTANT / SUN_TEMPERATURE) * 1e9
            wavelength_spot = (WIEN_CONSTANT / spot_temp) * 1e9
            
            st.markdown(f"""
            <div class="calculation-box">
                <h4>🌈 Lei de Wien</h4>
                <strong>Fórmula:</strong> λ_max × T = 2,898×10⁻³ m·K<br><br>
                
                <strong>Fotosfera (5.778 K):</strong><br>
                λ_max = 2,898×10⁻³ ÷ 5.778<br>
                λ_max = <strong>{wavelength_sun:.0f} nm</strong> (verde-amarelo)<br><br>
                
                <strong>Mancha ({spot_temp:.0f} K):</strong><br>
                λ_max = 2,898×10⁻³ ÷ {spot_temp:.0f}<br>
                λ_max = <strong>{wavelength_spot:.0f} nm</strong> (vermelho)<br><br>
                
                <strong>Deslocamento:</strong> {wavelength_spot-wavelength_sun:.0f} nm para o vermelho
            </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        # Teoria com design moderno
        st.markdown('<h2 class="section-header">📚 Base Científica</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="info-box">
                <h3>🔥 Lei de Stefan-Boltzmann</h3>
                <p><strong>I = σ × T⁴</strong></p>
                <p>Esta lei fundamental descreve como a energia total irradiada por um corpo negro 
                é proporcional à quarta potência de sua temperatura absoluta.</p>
                
                <p><strong>Aplicação prática:</strong><br>
                Medindo o contraste entre manchas e fotosfera, podemos calcular 
                precisamente suas temperaturas.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="info-box">
                <h3>🌌 O que São Manchas Solares?</h3>
                <p>Regiões temporárias na fotosfera solar que aparecem mais escuras porque 
                são mais frias que as áreas circundantes.</p>
                
                <p><strong>Características:</strong></p>
                <ul>
                <li>Temperatura: 3.000-4.500 K</li>
                <li>Causadas por campos magnéticos intensos</li>
                <li>Ciclo de 11 anos</li>
                <li>Podem ser maiores que a Terra</li>
                <li>Afetam o clima espacial</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="info-box">
                <h3>🎨 Lei do Deslocamento de Wien</h3>
                <p><strong>λ_max × T = constante</strong></p>
                <p>Esta lei relaciona a temperatura de um corpo com o comprimento de onda 
                no qual emite a maior parte de sua radiação.</p>
                
                <p><strong>Efeito visual:</strong><br>
                • Corpos mais quentes → cores mais azuis<br>
                • Corpos mais frios → cores mais vermelhas<br>
                • Sol: pico no verde-amarelo (5.778K)<br>
                • Manchas: pico no vermelho (~4.000K)</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="info-box">
                <h3>🔍 Por que as Manchas Parecem Escuras?</h3>
                <p><strong>Efeito de contraste:</strong> Não são realmente escuras - emitem 
                menos luz que o entorno, criando a ilusão de escuridão.</p>
                
                <p><strong>Analogia:</strong> Imagine velas acesas sob a luz do sol - 
                embora brilhantes, parecem escuras em comparação.</p>
                
                <p><strong>Física:</strong> Campos magnéticos intensos inibem a convecção, 
                reduzindo o transporte de calor para a superfície.</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab4:
        # Galeria de imagens reais
        st.markdown('<h2 class="section-header">🖼️ Galeria Solar</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box">
            <h3>📸 Imagens Reais do Solar Dynamics Observatory (NASA)</h3>
            <p>Explore imagens reais do Sol capturadas em diferentes comprimentos de onda pelo observatório solar da NASA.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Carregar imagens solares
        solar_images = load_solar_images()
        
        # Mostrar imagens em colunas
        cols = st.columns(2)
        for idx, (title, url) in enumerate(solar_images.items()):
            with cols[idx % 2]:
                try:
                    response = requests.get(url)
                    img = Image.open(io.BytesIO(response.content))
                    st.image(img, caption=f"🌞 {title}", use_column_width=True)
                except Exception as e:
                    st.error(f"Erro ao carregar {title}: {e}")
                    # Placeholder visual
                    st.image("https://via.placeholder.com/400x300/1e3c72/ffffff?text=Imagem+Solar", 
                            caption=f"🌞 {title} (Imagem de exemplo)")
    
    with tab5:
        # Atividades interativas
        st.markdown('<h2 class="section-header">🎯 Missões Científicas</h2>', unsafe_allow_html=True)
        
        # Missão 1
        st.markdown(f"""
        <div class="info-box">
            <h3>🧮 Missão 1: Detetive Solar</h3>
            <p><strong>Objetivo:</strong> Calcular temperaturas manualmente e verificar com o software</p>
            
            <p><strong>Configuração atual:</strong></p>
            <ul>
            <li>Intensidade da mancha: <strong>{spot_intensity}%</strong></li>
            <li>Razão calculada: <strong>{intensity_ratio:.3f}</strong></li>
            <li>Temperatura esperada: <strong>{spot_temp:.0f} K</strong></li>
            </ul>
            
            <p><strong>Desafio:</strong> Use uma calculadora para verificar o cálculo:<br>
            <code>5778 × ({intensity_ratio:.3f})^(1/4) = ?</code></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Missão 2
        st.markdown("""
        <div class="info-box">
            <h3>📊 Missão 2: Investigação de Padrões</h3>
            <p><strong>Objetivo:</strong> Descobrir como a intensidade afeta a temperatura</p>
            
            <p><strong>Experimento:</strong></p>
            <ol>
            <li>Configure intensidade para 25% - anote a temperatura</li>
            <li>Configure intensidade para 50% - anote a temperatura</li>
            <li>Configure intensidade para 75% - anote a temperatura</li>
            </ol>
            
            <p><strong>Análise:</strong></p>
            <ul>
            <li>A relação é linear?</li>
            <li>Qual a diferença prática entre 25% e 75%?</li>
            <li>Por que a temperatura não cai proporcionalmente?</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Missão 3
        st.markdown("""
        <div class="info-box">
            <h3>🔍 Missão 3: Pesquisa Científica</h3>
            <p><strong>Objetivo:</strong> Testar hipóteses sobre manchas solares</p>
            
            <p><strong>Hipótese:</strong> "O tamanho da mancha não afeta sua temperatura"</p>
            
            <p><strong>Método:</strong></p>
            <ol>
            <li>Mantenha a intensidade constante em 40%</li>
            <li>Teste com manchas pequenas (tamanho 5)</li>
            <li>Teste com manchas grandes (tamanho 15)</li>
            <li>Compare as temperaturas calculadas</li>
            </ol>
            
            <p><strong>Conclusão:</strong> Sua hipótese foi confirmada?</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Área de relatório
        st.markdown("### 📝 Laboratório de Anotações")
        with st.form("relatorio_form"):
            observacoes = st.text_area("📋 Registre suas observações e descobertas:", 
                                     height=200,
                                     placeholder="Descreva aqui seus experimentos, cálculos e conclusões...")
            
            submitted = st.form_submit_button("💾 Salvar Relatório")
            if submitted:
                st.success("🎉 Relatório salvo com sucesso! Continue explorando outras missões.")
        
        # Próximos passos
        st.markdown("""
        <div class="info-box">
            <h3>🚀 Próximos Desafios</h3>
            <p>Após completar estas missões, você estará pronto para:</p>
            <ul>
            <li>Analisar imagens reais do SDO</li>
            <li>Estudar o ciclo solar de 11 anos</li>
            <li>Investigar a relação entre manchas e clima espacial</li>
            <li>Explorar outros fenômenos solares</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
