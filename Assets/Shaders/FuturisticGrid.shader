Shader "Custom/FuturisticGrid"
{
    Properties
    {
        _GridColor       ("Grid Line Color",   Color)  = (0.0, 0.9, 1.0, 1.0)
        _BackgroundColor ("Background Color",  Color)  = (0.0, 0.04, 0.08, 0.0)
        _GridSize        ("Grid Size (m)",     Float)  = 0.5
        _LineWidth       ("Line Width (m)",    Float)  = 0.02
        _GlowFalloff     ("Glow Falloff",      Float)  = 12.0
        _GlowIntensity   ("Glow Intensity",    Float)  = 3.0
        _PulseSpeed      ("Pulse Speed",       Float)  = 1.2
        _PulseAmount     ("Pulse Amount",      Float)  = 0.1
    }

    SubShader
    {
        Tags
        {
            "RenderType"     = "Transparent"
            "Queue"          = "Transparent"
            "RenderPipeline" = "UniversalPipeline"
        }

        Pass
        {
            Name "SRPDefaultUnlit"
            Tags { "LightMode" = "SRPDefaultUnlit" }

            Blend SrcAlpha One
            ZWrite Off
            Cull Off

            HLSLPROGRAM
            #pragma vertex   vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #pragma instancing_options renderingLayer

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float4 _GridColor;
                float4 _BackgroundColor;
                float  _GridSize;
                float  _LineWidth;
                float  _GlowFalloff;
                float  _GlowIntensity;
                float  _PulseSpeed;
                float  _PulseAmount;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionHCS : SV_POSITION;
                float3 worldPos    : TEXCOORD0;
                float3 worldNormal : TEXCOORD1;
                UNITY_VERTEX_INPUT_INSTANCE_ID
                UNITY_VERTEX_OUTPUT_STEREO
            };

            // Signed distance from nearest world-grid line along one axis (0=at line, 0.5=center)
            float GridLine1D(float coord, float gridSize, float lineHalfWidth, float glowFalloff)
            {
                float f = abs(frac(coord / gridSize + 0.5) - 0.5); // 0=at line, 0.5=center
                float distFromLine = f * gridSize;                  // distance in world units
                float hardLine = 1.0 - smoothstep(0.0, lineHalfWidth, distFromLine);
                float glowLine  = exp(-distFromLine * glowFalloff);
                return saturate(hardLine + glowLine * 0.4);
            }

            Varyings vert(Attributes IN)
            {
                Varyings OUT;
                UNITY_SETUP_INSTANCE_ID(IN);
                UNITY_TRANSFER_INSTANCE_ID(IN, OUT);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(OUT);

                float3 posWS    = TransformObjectToWorld(IN.positionOS.xyz);
                OUT.positionHCS = TransformWorldToHClip(posWS);
                OUT.worldPos    = posWS;
                OUT.worldNormal = TransformObjectToWorldNormal(IN.normalOS);
                return OUT;
            }

            half4 frag(Varyings IN) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(IN);
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(IN);

                float3 wpos = IN.worldPos;
                float3 N    = abs(normalize(IN.worldNormal));

                // Triplanar blend: each plane weighted by how dominant that normal axis is
                float3 blend = pow(N, 8.0);
                blend /= max(dot(blend, float3(1, 1, 1)), 0.0001);

                float lhw = _LineWidth * 0.5;
                float gf  = _GlowFalloff;
                float gs  = _GridSize;

                float gX = GridLine1D(wpos.x, gs, lhw, gf);
                float gY = GridLine1D(wpos.y, gs, lhw, gf);
                float gZ = GridLine1D(wpos.z, gs, lhw, gf);

                // Per-plane grid: use the two axes tangent to each surface
                // Normal=Y (floor/ceil) -> XZ grid  | Normal=X (side walls) -> YZ grid  | Normal=Z (back wall) -> XY grid
                float gXY = max(gX, gY);
                float gXZ = max(gX, gZ);
                float gYZ = max(gY, gZ);

                float grid = blend.x * gYZ + blend.y * gXZ + blend.z * gXY;

                float pulse        = 1.0 + _PulseAmount * sin(_Time.y * _PulseSpeed);
                float3 gridEmit    = _GridColor.rgb * _GlowIntensity * pulse;

                float3 color = lerp(_BackgroundColor.rgb, gridEmit, grid);
                float  alpha = lerp(_BackgroundColor.a,   _GridColor.a, grid);

                return half4(color, alpha);
            }
            ENDHLSL
        }
    }
}
