struct keys_a_buffer {
    member: array<u32>,
}

struct histogram_buffer {
    member: array<u32>,
}

struct build_histogram_push {
    num_elements: u32,
    current_shift: u32,
    num_workgroups: u32,
    num_blocks_per_workgroup: u32,
}

struct payload_a_buffer {
    member: array<u32>,
}

struct keys_b_buffer {
    member: array<u32>,
}

struct payload_b_buffer {
    member: array<u32>,
}

struct scatter_keys_push {
    num_elements: u32,
    current_shift: u32,
    num_workgroups: u32,
    num_blocks_per_workgroup: u32,
}

@group(0) @binding(0) 
var<storage, read_write> keys_a: keys_a_buffer;
@group(0) @binding(1) 
var<storage, read_write> histogram: histogram_buffer;
@group(0) @binding(30) 
var<uniform> build_histogram_args: build_histogram_push;
var<workgroup> SHARED_HISTOGRAM: array<atomic<u32>, 256>;
var<private> gl_LocalInvocationId_2: vec3<u32>;
var<private> gl_WorkgroupId_2: vec3<u32>;
@group(0) @binding(0) 
var<storage, read_write> keys_a_1: keys_a_buffer;
@group(0) @binding(1) 
var<storage, read_write> histogram_1: histogram_buffer;
@group(0) @binding(2) 
var<storage, read_write> payload_a: payload_a_buffer;
@group(0) @binding(3) 
var<storage, read_write> keys_b: keys_b_buffer;
@group(0) @binding(4) 
var<storage, read_write> payload_b: payload_b_buffer;
@group(0) @binding(30) 
var<uniform> scatter_keys_args: scatter_keys_push;
var<workgroup> SHARED_BIN_FLAGS: array<atomic<u32>, 2048>;
var<workgroup> SHARED_GLOBAL_OFFSETS: array<atomic<u32>, 256>;
var<workgroup> SHARED_BUCKET_COUNTS: array<u32, 256>;
var<workgroup> SHARED_BUCKET_PREFIX: array<u32, 256>;

fn build_histogram_1() {
    var local: u32;
    var local_1: u32;
    var local_2: u32;
    var local_3: u32;
    var local_4: u32;
    var local_5: u32;
    var local_6: u32;
    var local_7: u32;
    var local_8: u32;
    var local_9: u32;
    var local_10: u32;
    var local_11: u32;
    var local_12: u32;
    var local_13: u32;
    var local_14: u32;
    var local_15: u32;
    var local_16: u32;
    var local_17: u32;
    var local_18: u32;
    var local_19: u32;
    var local_20: u32;
    var local_21: u32;
    var local_22: u32;
    var local_23: u32;
    var local_24: u32;
    var local_25: u32;
    var local_26: u32;
    var local_27: u32;
    var local_28: u32;
    var local_29: u32;
    var local_30: u32;
    var local_31: u32;
    var local_32: u32;
    var local_33: u32;
    var local_34: u32;
    var local_35: u32;
    var local_36: u32;
    var local_37: u32;
    var local_38: u32;
    var local_39: u32;
    var local_40: u32;
    var local_41: u32;
    var local_42: u32;
    var local_43: u32;
    var local_44: u32;
    var local_45: u32;
    var local_46: u32;

    local = 0u;
    local_1 = 0u;
    let _e76 = build_histogram_args.num_elements;
    local_2 = _e76;
    let _e78 = build_histogram_args.current_shift;
    local_3 = _e78;
    let _e80 = build_histogram_args.num_workgroups;
    local_4 = _e80;
    let _e82 = build_histogram_args.num_blocks_per_workgroup;
    local_5 = _e82;
    let _e84 = gl_LocalInvocationId_2[0u];
    local_6 = _e84;
    let _e85 = local_6;
    local_7 = _e85;
    let _e87 = gl_WorkgroupId_2[0u];
    local_8 = _e87;
    let _e88 = local_8;
    local_9 = _e88;
    let _e89 = local_7;
    local_10 = _e89;
    let _e90 = local_10;
    local_11 = _e90;
    let _e91 = local_11;
    local_12 = (_e91 * 4u);
    let _e93 = local_12;
    atomicStore((&SHARED_HISTOGRAM[(_e93 >> bitcast<u32>(2u))]), 0u);
    workgroupBarrier();
    let _e97 = local_5;
    local_13 = _e97;
    local_14 = 0u;
    loop {
        let _e98 = local_14;
        let _e99 = local_13;
        local_15 = select(0u, 1u, (_e98 < _e99));
        let _e102 = local_15;
        if (_e102 == 0u) {
            break;
        }
        let _e104 = local_9;
        let _e105 = local_5;
        local_16 = (_e104 * _e105);
        let _e107 = local_16;
        local_17 = (_e107 * 256u);
        let _e109 = local_14;
        local_18 = (_e109 * 256u);
        let _e111 = local_17;
        let _e112 = local_18;
        local_19 = (_e111 + _e112);
        let _e114 = local_19;
        let _e115 = local_7;
        local_20 = (_e114 + _e115);
        let _e117 = local_20;
        local_21 = _e117;
        let _e118 = local_21;
        let _e119 = local_2;
        local_22 = select(0u, 1u, (_e118 < _e119));
        let _e122 = local_22;
        if (_e122 == 0u) {
        } else {
            let _e124 = local_21;
            local_23 = _e124;
            let _e125 = local_23;
            local_24 = _e125;
            let _e126 = local_24;
            local_25 = (_e126 * 4u);
            let _e128 = local;
            let _e129 = local_25;
            local_26 = (_e128 + _e129);
            let _e131 = local_26;
            let _e136 = keys_a.member[(_e131 >> bitcast<u32>(2u))];
            local_27 = _e136;
            let _e137 = local_27;
            let _e138 = local_3;
            local_28 = (_e137 >> bitcast<u32>((_e138 & 31u)));
            let _e142 = local_28;
            local_29 = (_e142 & 255u);
            let _e144 = local_29;
            local_30 = _e144;
            let _e145 = local_30;
            local_31 = _e145;
            let _e146 = local_31;
            local_32 = _e146;
            let _e147 = local_32;
            local_33 = (_e147 * 4u);
            let _e149 = local_33;
            let _e153 = atomicAdd((&SHARED_HISTOGRAM[(_e149 >> bitcast<u32>(2u))]), 1u);
            local_34 = _e153;
        }
        let _e154 = local_14;
        local_35 = _e154;
        let _e155 = local_14;
        local_36 = (_e155 + 1u);
        let _e157 = local_36;
        local_14 = _e157;
        continue;
    }
    workgroupBarrier();
    let _e158 = local_7;
    local_37 = _e158;
    let _e159 = local_37;
    local_38 = _e159;
    let _e160 = local_38;
    local_39 = (_e160 * 4u);
    let _e162 = local_39;
    let _e166 = atomicLoad((&SHARED_HISTOGRAM[(_e162 >> bitcast<u32>(2u))]));
    local_40 = _e166;
    let _e167 = local_9;
    local_41 = (256u * _e167);
    let _e169 = local_41;
    let _e170 = local_7;
    local_42 = (_e169 + _e170);
    let _e172 = local_42;
    local_43 = _e172;
    let _e173 = local_43;
    local_44 = _e173;
    let _e174 = local_44;
    local_45 = (_e174 * 4u);
    let _e176 = local_1;
    let _e177 = local_45;
    local_46 = (_e176 + _e177);
    let _e179 = local_46;
    let _e184 = local_40;
    histogram.member[(_e179 >> bitcast<u32>(2u))] = _e184;
    return;
}

fn scatter_keys_1() {
    var local_47: u32;
    var local_48: u32;
    var local_49: u32;
    var local_50: u32;
    var local_51: u32;
    var local_52: u32;
    var local_53: u32;
    var local_54: u32;
    var local_55: u32;
    var local_56: u32;
    var local_57: u32;
    var local_58: u32;
    var local_59: u32;
    var local_60: u32;
    var local_61: u32;
    var local_62: u32;
    var local_63: u32;
    var local_64: u32;
    var local_65: u32;
    var local_66: u32;
    var local_67: u32;
    var local_68: u32;
    var local_69: u32;
    var local_70: u32;
    var local_71: u32;
    var local_72: u32;
    var local_73: u32;
    var local_74: u32;
    var local_75: u32;
    var local_76: u32;
    var local_77: u32;
    var local_78: u32;
    var local_79: u32;
    var local_80: u32;
    var local_81: u32;
    var local_82: u32;
    var local_83: u32;
    var local_84: u32;
    var local_85: u32;
    var local_86: u32;
    var local_87: u32;
    var local_88: u32;
    var local_89: u32;
    var local_90: u32;
    var local_91: u32;
    var local_92: u32;
    var local_93: u32;
    var local_94: u32;
    var local_95: u32;
    var local_96: u32;
    var local_97: u32;
    var local_98: u32;
    var local_99: u32;
    var local_100: u32;
    var local_101: u32;
    var local_102: u32;
    var local_103: u32;
    var local_104: u32;
    var local_105: u32;
    var local_106: u32;
    var local_107: u32;
    var local_108: u32;
    var local_109: u32;
    var local_110: u32;
    var local_111: u32;
    var local_112: u32;
    var local_113: u32;
    var local_114: u32;
    var local_115: u32;
    var local_116: u32;
    var local_117: u32;
    var local_118: u32;
    var local_119: u32;
    var local_120: u32;
    var local_121: u32;
    var local_122: u32;
    var local_123: u32;
    var local_124: u32;
    var local_125: u32;
    var local_126: u32;
    var local_127: u32;
    var local_128: u32;
    var local_129: u32;
    var local_130: u32;
    var local_131: u32;
    var local_132: u32;
    var local_133: u32;
    var local_134: u32;
    var local_135: u32;
    var local_136: u32;
    var local_137: u32;
    var local_138: u32;
    var local_139: u32;
    var local_140: u32;
    var local_141: u32;
    var local_142: u32;
    var local_143: u32;
    var local_144: u32;
    var local_145: u32;
    var local_146: u32;
    var local_147: u32;
    var local_148: u32;
    var local_149: u32;
    var local_150: u32;
    var local_151: u32;
    var local_152: u32;
    var local_153: u32;
    var local_154: u32;
    var local_155: u32;
    var local_156: u32;
    var local_157: u32;
    var local_158: u32;
    var local_159: u32;
    var local_160: u32;
    var local_161: u32;
    var local_162: u32;
    var local_163: u32;
    var local_164: u32;
    var local_165: u32;
    var local_166: u32;
    var local_167: u32;
    var local_168: u32;
    var local_169: u32;
    var local_170: u32;
    var local_171: u32;
    var local_172: u32;
    var local_173: u32;
    var local_174: u32;
    var local_175: u32;
    var local_176: u32;
    var local_177: u32;
    var local_178: u32;
    var local_179: u32;
    var local_180: u32;
    var local_181: u32;
    var local_182: u32;
    var local_183: u32;
    var local_184: u32;
    var local_185: u32;
    var local_186: u32;
    var local_187: u32;
    var local_188: u32;
    var local_189: u32;
    var local_190: u32;
    var local_191: u32;

    local_47 = 0u;
    local_48 = 0u;
    local_49 = 0u;
    local_50 = 0u;
    local_51 = 0u;
    let _e174 = scatter_keys_args.num_elements;
    local_52 = _e174;
    let _e176 = scatter_keys_args.current_shift;
    local_53 = _e176;
    let _e178 = scatter_keys_args.num_workgroups;
    local_54 = _e178;
    let _e180 = scatter_keys_args.num_blocks_per_workgroup;
    local_55 = _e180;
    let _e182 = gl_LocalInvocationId_2[0u];
    local_56 = _e182;
    let _e183 = local_56;
    local_57 = _e183;
    let _e185 = gl_WorkgroupId_2[0u];
    local_58 = _e185;
    let _e186 = local_58;
    local_59 = _e186;
    local_60 = 0u;
    local_61 = 0u;
    let _e187 = local_54;
    local_62 = _e187;
    local_63 = 0u;
    loop {
        let _e188 = local_63;
        let _e189 = local_62;
        local_64 = select(0u, 1u, (_e188 < _e189));
        let _e192 = local_64;
        if (_e192 == 0u) {
            break;
        }
        let _e194 = local_63;
        local_65 = (_e194 * 256u);
        let _e196 = local_65;
        let _e197 = local_57;
        local_66 = (_e196 + _e197);
        let _e199 = local_66;
        local_67 = _e199;
        let _e200 = local_67;
        local_68 = _e200;
        let _e201 = local_68;
        local_69 = (_e201 * 4u);
        let _e203 = local_48;
        let _e204 = local_69;
        local_70 = (_e203 + _e204);
        let _e206 = local_70;
        let _e211 = histogram_1.member[(_e206 >> bitcast<u32>(2u))];
        local_71 = _e211;
        let _e212 = local_71;
        local_72 = _e212;
        let _e213 = local_63;
        let _e214 = local_59;
        local_73 = select(0u, 1u, (_e213 == _e214));
        let _e217 = local_73;
        if (_e217 == 0u) {
        } else {
            let _e219 = local_61;
            local_60 = _e219;
        }
        let _e220 = local_61;
        let _e221 = local_72;
        local_74 = (_e220 + _e221);
        let _e223 = local_74;
        local_61 = _e223;
        let _e224 = local_63;
        local_75 = _e224;
        let _e225 = local_63;
        local_76 = (_e225 + 1u);
        let _e227 = local_76;
        local_63 = _e227;
        continue;
    }
    let _e228 = local_57;
    local_77 = _e228;
    let _e229 = local_77;
    local_78 = _e229;
    let _e230 = local_78;
    let _e232 = local_61;
    SHARED_BUCKET_COUNTS[_e230] = _e232;
    workgroupBarrier();
    let _e233 = local_57;
    local_79 = select(0u, 1u, (_e233 == 0u));
    let _e236 = local_79;
    if (_e236 == 0u) {
    } else {
        local_80 = 0u;
        local_81 = 0u;
        loop {
            let _e238 = local_81;
            local_82 = select(0u, 1u, (_e238 < 256u));
            let _e241 = local_82;
            if (_e241 == 0u) {
                break;
            } else {
                let _e243 = local_81;
                local_83 = _e243;
                let _e244 = local_83;
                local_84 = _e244;
                let _e245 = local_84;
                let _e247 = local_80;
                SHARED_BUCKET_PREFIX[_e245] = _e247;
                let _e248 = local_81;
                local_85 = _e248;
                let _e249 = local_85;
                local_86 = _e249;
                let _e250 = local_86;
                let _e252 = SHARED_BUCKET_COUNTS[_e250];
                local_87 = _e252;
                let _e253 = local_80;
                let _e254 = local_87;
                local_88 = (_e253 + _e254);
                let _e256 = local_88;
                local_80 = _e256;
                let _e257 = local_81;
                local_89 = _e257;
                let _e258 = local_81;
                local_90 = (_e258 + 1u);
                let _e260 = local_90;
                local_81 = _e260;
                continue;
            }
        }
    }
    workgroupBarrier();
    let _e261 = local_57;
    local_91 = _e261;
    let _e262 = local_91;
    local_92 = _e262;
    let _e263 = local_92;
    let _e265 = SHARED_BUCKET_PREFIX[_e263];
    local_93 = _e265;
    let _e266 = local_93;
    let _e267 = local_60;
    local_94 = (_e266 + _e267);
    let _e269 = local_94;
    local_95 = _e269;
    let _e270 = local_57;
    local_96 = _e270;
    let _e271 = local_96;
    local_97 = _e271;
    let _e272 = local_97;
    local_98 = (_e272 * 4u);
    let _e274 = local_98;
    let _e278 = local_95;
    atomicStore((&SHARED_GLOBAL_OFFSETS[(_e274 >> bitcast<u32>(2u))]), _e278);
    let _e279 = local_57;
    local_99 = (_e279 / 32u);
    let _e281 = local_99;
    local_100 = _e281;
    let _e282 = local_57;
    local_101 = (_e282 % 32u);
    let _e284 = local_101;
    local_102 = (1u << bitcast<u32>((_e284 & 31u)));
    let _e288 = local_102;
    local_103 = _e288;
    let _e289 = local_55;
    local_104 = _e289;
    local_105 = 0u;
    loop {
        let _e290 = local_105;
        let _e291 = local_104;
        local_106 = select(0u, 1u, (_e290 < _e291));
        let _e294 = local_106;
        if (_e294 == 0u) {
            break;
        }
        let _e296 = local_59;
        let _e297 = local_55;
        local_107 = (_e296 * _e297);
        let _e299 = local_107;
        local_108 = (_e299 * 256u);
        let _e301 = local_105;
        local_109 = (_e301 * 256u);
        let _e303 = local_108;
        let _e304 = local_109;
        local_110 = (_e303 + _e304);
        let _e306 = local_110;
        let _e307 = local_57;
        local_111 = (_e306 + _e307);
        let _e309 = local_111;
        local_112 = _e309;
        local_113 = 0u;
        loop {
            let _e310 = local_113;
            local_114 = select(0u, 1u, (_e310 < 8u));
            let _e313 = local_114;
            if (_e313 == 0u) {
                break;
            } else {
                let _e315 = local_57;
                local_115 = (_e315 * 8u);
                let _e317 = local_115;
                let _e318 = local_113;
                local_116 = (_e317 + _e318);
                let _e320 = local_116;
                local_117 = _e320;
                let _e321 = local_117;
                local_118 = _e321;
                let _e322 = local_118;
                local_119 = (_e322 * 4u);
                let _e324 = local_119;
                atomicStore((&SHARED_BIN_FLAGS[(_e324 >> bitcast<u32>(2u))]), 0u);
                let _e328 = local_113;
                local_120 = _e328;
                let _e329 = local_113;
                local_121 = (_e329 + 1u);
                let _e331 = local_121;
                local_113 = _e331;
                continue;
            }
        }
        workgroupBarrier();
        local_122 = 0u;
        local_123 = 0u;
        local_124 = 0u;
        local_125 = 0u;
        let _e332 = local_112;
        let _e333 = local_52;
        local_126 = select(0u, 1u, (_e332 < _e333));
        let _e336 = local_126;
        if (_e336 == 0u) {
        } else {
            let _e338 = local_112;
            local_127 = _e338;
            let _e339 = local_127;
            local_128 = _e339;
            let _e340 = local_128;
            local_129 = (_e340 * 4u);
            let _e342 = local_47;
            let _e343 = local_129;
            local_130 = (_e342 + _e343);
            let _e345 = local_130;
            let _e350 = keys_a_1.member[(_e345 >> bitcast<u32>(2u))];
            local_131 = _e350;
            let _e351 = local_131;
            local_122 = _e351;
            let _e352 = local_112;
            local_132 = _e352;
            let _e353 = local_132;
            local_133 = _e353;
            let _e354 = local_133;
            local_134 = (_e354 * 4u);
            let _e356 = local_49;
            let _e357 = local_134;
            local_135 = (_e356 + _e357);
            let _e359 = local_135;
            let _e364 = payload_a.member[(_e359 >> bitcast<u32>(2u))];
            local_136 = _e364;
            let _e365 = local_136;
            local_123 = _e365;
            let _e366 = local_122;
            let _e367 = local_53;
            local_137 = (_e366 >> bitcast<u32>((_e367 & 31u)));
            let _e371 = local_137;
            local_138 = (_e371 & 255u);
            let _e373 = local_138;
            local_124 = _e373;
            let _e374 = local_124;
            local_139 = _e374;
            let _e375 = local_139;
            local_140 = _e375;
            let _e376 = local_140;
            local_141 = (_e376 * 4u);
            let _e378 = local_141;
            let _e382 = atomicLoad((&SHARED_GLOBAL_OFFSETS[(_e378 >> bitcast<u32>(2u))]));
            local_142 = _e382;
            let _e383 = local_142;
            local_125 = _e383;
            let _e384 = local_124;
            local_143 = (_e384 * 8u);
            let _e386 = local_143;
            let _e387 = local_100;
            local_144 = (_e386 + _e387);
            let _e389 = local_144;
            local_145 = _e389;
            let _e390 = local_145;
            local_146 = _e390;
            let _e391 = local_146;
            local_147 = (_e391 * 4u);
            let _e393 = local_147;
            let _e397 = local_103;
            let _e398 = atomicOr((&SHARED_BIN_FLAGS[(_e393 >> bitcast<u32>(2u))]), _e397);
            local_148 = _e398;
        }
        workgroupBarrier();
        let _e399 = local_112;
        let _e400 = local_52;
        local_149 = select(0u, 1u, (_e399 < _e400));
        let _e403 = local_149;
        if (_e403 == 0u) {
        } else {
            local_150 = 0u;
            local_151 = 0u;
            local_152 = 0u;
            loop {
                let _e405 = local_152;
                local_153 = select(0u, 1u, (_e405 < 8u));
                let _e408 = local_153;
                if (_e408 == 0u) {
                    break;
                }
                local_154 = 0u;
                let _e410 = local_124;
                local_155 = (_e410 * 8u);
                let _e412 = local_155;
                let _e413 = local_152;
                local_156 = (_e412 + _e413);
                let _e415 = local_156;
                local_157 = _e415;
                let _e416 = local_157;
                local_158 = _e416;
                let _e417 = local_158;
                local_159 = (_e417 * 4u);
                let _e419 = local_159;
                let _e423 = atomicLoad((&SHARED_BIN_FLAGS[(_e419 >> bitcast<u32>(2u))]));
                local_160 = _e423;
                let _e424 = local_160;
                local_154 = _e424;
                let _e425 = local_154;
                local_161 = countOneBits(_e425);
                let _e427 = local_161;
                local_162 = _e427;
                let _e428 = local_103;
                local_163 = (_e428 - 1u);
                let _e430 = local_154;
                let _e431 = local_163;
                local_164 = (_e430 & _e431);
                let _e433 = local_164;
                local_165 = countOneBits(_e433);
                let _e435 = local_165;
                local_166 = _e435;
                let _e436 = local_152;
                let _e437 = local_100;
                local_167 = select(0u, 1u, (_e436 < _e437));
                let _e440 = local_167;
                if (_e440 == 0u) {
                } else {
                    let _e442 = local_150;
                    let _e443 = local_162;
                    local_168 = (_e442 + _e443);
                    let _e445 = local_168;
                    local_150 = _e445;
                }
                let _e446 = local_152;
                let _e447 = local_100;
                local_169 = select(0u, 1u, (_e446 == _e447));
                let _e450 = local_169;
                if (_e450 == 0u) {
                } else {
                    let _e452 = local_150;
                    let _e453 = local_166;
                    local_170 = (_e452 + _e453);
                    let _e455 = local_170;
                    local_150 = _e455;
                }
                let _e456 = local_151;
                let _e457 = local_162;
                local_171 = (_e456 + _e457);
                let _e459 = local_171;
                local_151 = _e459;
                let _e460 = local_152;
                local_172 = _e460;
                let _e461 = local_152;
                local_173 = (_e461 + 1u);
                let _e463 = local_173;
                local_152 = _e463;
                continue;
            }
            let _e464 = local_125;
            let _e465 = local_150;
            local_174 = (_e464 + _e465);
            let _e467 = local_174;
            local_175 = _e467;
            let _e468 = local_175;
            local_176 = _e468;
            let _e469 = local_176;
            local_177 = (_e469 * 4u);
            let _e471 = local_50;
            let _e472 = local_177;
            local_178 = (_e471 + _e472);
            let _e474 = local_178;
            let _e479 = local_122;
            keys_b.member[(_e474 >> bitcast<u32>(2u))] = _e479;
            let _e480 = local_125;
            let _e481 = local_150;
            local_179 = (_e480 + _e481);
            let _e483 = local_179;
            local_180 = _e483;
            let _e484 = local_180;
            local_181 = _e484;
            let _e485 = local_181;
            local_182 = (_e485 * 4u);
            let _e487 = local_51;
            let _e488 = local_182;
            local_183 = (_e487 + _e488);
            let _e490 = local_183;
            let _e495 = local_123;
            payload_b.member[(_e490 >> bitcast<u32>(2u))] = _e495;
            let _e496 = local_151;
            local_184 = (_e496 - 1u);
            let _e498 = local_150;
            let _e499 = local_184;
            local_185 = select(0u, 1u, (_e498 == _e499));
            let _e502 = local_185;
            if (_e502 == 0u) {
            } else {
                let _e504 = local_124;
                local_186 = _e504;
                let _e505 = local_186;
                local_187 = _e505;
                let _e506 = local_187;
                local_188 = (_e506 * 4u);
                let _e508 = local_188;
                let _e512 = local_151;
                let _e513 = atomicAdd((&SHARED_GLOBAL_OFFSETS[(_e508 >> bitcast<u32>(2u))]), _e512);
                local_189 = _e513;
            }
        }
        workgroupBarrier();
        let _e514 = local_105;
        local_190 = _e514;
        let _e515 = local_105;
        local_191 = (_e515 + 1u);
        let _e517 = local_191;
        local_105 = _e517;
        continue;
    }
    return;
}

@compute @workgroup_size(256, 1, 1) 
fn build_histogram(@builtin(local_invocation_id) gl_LocalInvocationId: vec3<u32>, @builtin(workgroup_id) gl_WorkgroupId: vec3<u32>) {
    gl_LocalInvocationId_2 = gl_LocalInvocationId;
    gl_WorkgroupId_2 = gl_WorkgroupId;
    build_histogram_1();
}

@compute @workgroup_size(256, 1, 1) 
fn scatter_keys(@builtin(local_invocation_id) gl_LocalInvocationId_1: vec3<u32>, @builtin(workgroup_id) gl_WorkgroupId_1: vec3<u32>) {
    gl_LocalInvocationId_2 = gl_LocalInvocationId_1;
    gl_WorkgroupId_2 = gl_WorkgroupId_1;
    scatter_keys_1();
}
