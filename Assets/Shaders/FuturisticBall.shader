Shader "Custom/FuturisticBall"
{
    Properties
    {
        _CoreColor        ("Core Color",         Color)  = (1, 0, 0, 1)
        _RimColor         ("Rim Color",          Color)  = (1, 0, 0, 1)
        _EmissionIntensity("Emission Intensity", Float)  = 3.0
        _FresnelPower     ("Fresnel Power",      Float)  = 2.5
        _FresnelStrength  ("Fresnel Strength",   Float)  = 2.0
        _PulseSpeed       ("Pulse Speed",        Float)  = 4.0
        _PulseAmount      ("Pulse Amount",       Float)  = 0.2
    }

    SubShader
    {
        Tags
        {
            "RenderType"     = "Transparent"
            "Queue"          = "Transparent"
            "RenderPipeline" = "UniversalPipeline"
        }

        // --- Pass 1: additive rim glow ---
        Pass
        {
            Name "RimGlow"
            Tags { "LightMode" = "UniversalForward" }

            Blend  SrcAlpha One   // additive — stacks light onto the scene
            ZWrite Off
            Cull   Back

            HLSLPROGRAM
            #pragma vertex   vert
            #pragma fragment frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float4 _CoreColor;
                float4 _RimColor;
                float  _EmissionIntensity;
                float  _FresnelPower;
                float  _FresnelStrength;
                float  _PulseSpeed;
                float  _PulseAmount;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 normalWS   : TEXCOORD0;
                float3 viewDirWS  : TEXCOORD1;
            };

            Varyings vert(Attributes IN)
            {
                Varyings OUT;
                float3 posWS   = TransformObjectToWorld(IN.positionOS.xyz);
                OUT.positionCS = TransformWorldToHClip(posWS);
                OUT.normalWS   = TransformObjectToWorldNormal(IN.normalOS);
                OUT.viewDirWS  = GetWorldSpaceViewDir(posWS);
                return OUT;
            }

            half4 frag(Varyings IN) : SV_Target
            {
                float3 N = normalize(IN.normalWS);
                float3 V = normalize(IN.viewDirWS);

                // Fresnel: 0 at center, 1 at silhouette edge
                float NdotV  = saturate(dot(N, V));
                float fresnel = pow(1.0 - NdotV, _FresnelPower);

                // Subtle pulse on the rim
                float pulse = 1.0 + _PulseAmount * sin(_Time.y * _PulseSpeed);

                // Inner core: dim, slightly transparent
                float3 core = _CoreColor.rgb * (1.0 - fresnel) * 0.35;

                // Outer rim: bright additive glow
                float3 rim  = _RimColor.rgb * _EmissionIntensity
                            * fresnel * _FresnelStrength * pulse;

                float3 color = core + rim;
                // Alpha strongest at rim, faint at centre
                float  alpha = saturate(fresnel * 0.85 + 0.12);

                return half4(color, alpha);
            }
            ENDHLSL
        }
    }
}
