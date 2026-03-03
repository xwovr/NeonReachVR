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

        Pass
        {
            Name "RimGlow"
            Tags { "LightMode" = "UniversalForward" }

            Blend  SrcAlpha One
            ZWrite Off
            Cull   Back

            HLSLPROGRAM
            #pragma vertex   vert
            #pragma fragment frag

            // Required for Single-Pass Instanced rendering on Meta Quest
            #pragma multi_compile_instancing
            #pragma instancing_options renderingLayer

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
                UNITY_VERTEX_INPUT_INSTANCE_ID  // stereo eye index source
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 normalWS   : TEXCOORD0;
                float3 viewDirWS  : TEXCOORD1;
                UNITY_VERTEX_INPUT_INSTANCE_ID  // needed for frag access
                UNITY_VERTEX_OUTPUT_STEREO      // routes output to the correct eye
            };

            Varyings vert(Attributes IN)
            {
                Varyings OUT;

                // Set up instancing and stereo eye for this vertex
                UNITY_SETUP_INSTANCE_ID(IN);
                UNITY_TRANSFER_INSTANCE_ID(IN, OUT);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(OUT);

                float3 posWS   = TransformObjectToWorld(IN.positionOS.xyz);
                OUT.positionCS = TransformWorldToHClip(posWS);
                OUT.normalWS   = TransformObjectToWorldNormal(IN.normalOS);
                OUT.viewDirWS  = GetWorldSpaceViewDir(posWS);
                return OUT;
            }

            half4 frag(Varyings IN) : SV_Target
            {
                // Resolve which eye this fragment belongs to
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(IN);

                float3 N = normalize(IN.normalWS);
                float3 V = normalize(IN.viewDirWS);

                float NdotV  = saturate(dot(N, V));
                float fresnel = pow(1.0 - NdotV, _FresnelPower);

                float pulse = 1.0 + _PulseAmount * sin(_Time.y * _PulseSpeed);

                float3 core = _CoreColor.rgb * (1.0 - fresnel) * 0.35;
                float3 rim  = _RimColor.rgb * _EmissionIntensity
                            * fresnel * _FresnelStrength * pulse;

                float3 color = core + rim;
                float  alpha = saturate(fresnel * 0.85 + 0.12);

                return half4(color, alpha);
            }
            ENDHLSL
        }
    }
}
