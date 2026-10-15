struct positions_buffer {
    member: array<f32>,
}

struct cell_ids_buffer {
    member: array<u32>,
}

struct object_ids_buffer {
    member: array<u32>,
}

struct radius_buffer {
    member: array<f32>,
}

struct build_cell_ids_array_push {
    cell_size: f32,
    num_particles: u32,
}

@group(0) @binding(0) 
var<storage, read_write> positions: positions_buffer;
@group(0) @binding(2) 
var<storage, read_write> cell_ids: cell_ids_buffer;
@group(0) @binding(3) 
var<storage, read_write> object_ids: object_ids_buffer;
@group(0) @binding(4) 
var<storage, read_write> radius: radius_buffer;
@group(0) @binding(30) 
var<uniform> build_cell_ids_array_args: build_cell_ids_array_push;
var<private> gl_GlobalInvocationId_1: vec3<u32>;

fn is_obj_in_cell(param: f32, param_1: f32, param_2: f32, param_3: u32, param_4: u32, param_5: f32) -> u32 {
    var local: f32;
    var local_1: f32;
    var local_2: f32;
    var local_3: u32;
    var local_4: u32;
    var local_5: f32;
    var local_6: f32;
    var local_7: f32;
    var local_8: f32;
    var local_9: f32;
    var local_10: f32;
    var local_11: f32;
    var local_12: f32;
    var local_13: f32;
    var local_14: f32;
    var local_15: f32;
    var local_16: f32;
    var local_17: f32;
    var local_18: f32;
    var local_19: f32;
    var local_20: f32;
    var local_21: f32;
    var local_22: f32;
    var local_23: f32;
    var local_24: f32;
    var local_25: f32;
    var local_26: f32;
    var local_27: f32;
    var local_28: f32;
    var local_29: u32;
    var local_30: u32;

    local = param;
    local_1 = param_1;
    local_2 = param_2;
    local_3 = param_3;
    local_4 = param_4;
    local_5 = param_5;
    let _e60 = local_3;
    local_6 = f32(_e60);
    let _e62 = local_6;
    let _e63 = local_5;
    local_7 = (_e62 * _e63);
    let _e65 = local_7;
    local_8 = _e65;
    let _e66 = local_4;
    local_9 = f32(_e66);
    let _e68 = local_9;
    let _e69 = local_5;
    local_10 = (_e68 * _e69);
    let _e71 = local_10;
    local_11 = _e71;
    let _e72 = local_8;
    let _e73 = local_5;
    local_12 = (_e72 + _e73);
    let _e75 = local_12;
    local_13 = _e75;
    let _e76 = local_11;
    let _e77 = local_5;
    local_14 = (_e76 + _e77);
    let _e79 = local_14;
    local_15 = _e79;
    let _e80 = local;
    let _e81 = local_8;
    local_16 = max(_e80, _e81);
    let _e83 = local_16;
    let _e84 = local_13;
    local_17 = min(_e83, _e84);
    let _e86 = local_17;
    local_18 = _e86;
    let _e87 = local_1;
    let _e88 = local_11;
    local_19 = max(_e87, _e88);
    let _e90 = local_19;
    let _e91 = local_15;
    local_20 = min(_e90, _e91);
    let _e93 = local_20;
    local_21 = _e93;
    let _e94 = local;
    let _e95 = local_18;
    local_22 = (_e94 - _e95);
    let _e97 = local_22;
    local_23 = _e97;
    let _e98 = local_1;
    let _e99 = local_21;
    local_24 = (_e98 - _e99);
    let _e101 = local_24;
    local_25 = _e101;
    let _e102 = local_23;
    let _e103 = local_23;
    local_26 = (_e102 * _e103);
    let _e105 = local_25;
    let _e106 = local_25;
    local_27 = (_e105 * _e106);
    let _e108 = local_26;
    let _e109 = local_27;
    local_28 = (_e108 + _e109);
    let _e111 = local_28;
    let _e112 = local_2;
    local_29 = select(0u, 1u, (_e111 < _e112));
    let _e115 = local_29;
    local_30 = select(0u, 1u, (_e115 != 0u));
    let _e118 = local_30;
    return _e118;
}

fn split_by_bits(param_6: u32) -> u32 {
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

    local_31 = param_6;
    let _e39 = local_31;
    local_32 = (_e39 & 65535u);
    let _e41 = local_32;
    local_33 = _e41;
    let _e42 = local_33;
    local_34 = (_e42 << bitcast<u32>((8u & 31u)));
    let _e46 = local_33;
    let _e47 = local_34;
    local_35 = (_e46 | _e47);
    let _e49 = local_35;
    local_36 = (_e49 & 16711935u);
    let _e51 = local_36;
    local_33 = _e51;
    let _e52 = local_33;
    local_37 = (_e52 << bitcast<u32>((4u & 31u)));
    let _e56 = local_33;
    let _e57 = local_37;
    local_38 = (_e56 | _e57);
    let _e59 = local_38;
    local_39 = (_e59 & 252645135u);
    let _e61 = local_39;
    local_33 = _e61;
    let _e62 = local_33;
    local_40 = (_e62 << bitcast<u32>((2u & 31u)));
    let _e66 = local_33;
    let _e67 = local_40;
    local_41 = (_e66 | _e67);
    let _e69 = local_41;
    local_42 = (_e69 & 858993459u);
    let _e71 = local_42;
    local_33 = _e71;
    let _e72 = local_33;
    local_43 = (_e72 << bitcast<u32>((1u & 31u)));
    let _e76 = local_33;
    let _e77 = local_43;
    local_44 = (_e76 | _e77);
    let _e79 = local_44;
    local_45 = (_e79 & 1431655765u);
    let _e81 = local_45;
    local_33 = _e81;
    let _e82 = local_33;
    return _e82;
}

fn morton_encode(param_7: u32, param_8: u32) -> u32 {
    var local_46: u32;
    var local_47: u32;
    var local_48: u32;
    var local_49: u32;
    var local_50: u32;
    var local_51: u32;
    var local_52: u32;
    var local_53: u32;

    local_46 = param_7;
    local_47 = param_8;
    let _e33 = local_46;
    local_48 = _e33;
    let _e34 = local_48;
    let _e35 = split_by_bits(_e34);
    local_49 = _e35;
    let _e36 = local_47;
    local_50 = _e36;
    let _e37 = local_50;
    let _e38 = split_by_bits(_e37);
    local_51 = _e38;
    let _e39 = local_51;
    local_52 = (_e39 << bitcast<u32>((1u & 31u)));
    let _e43 = local_49;
    let _e44 = local_52;
    local_53 = (_e43 | _e44);
    let _e46 = local_53;
    return _e46;
}

fn build_cell_ids_array_1() {
    var local_54: u32;
    var local_55: u32;
    var local_56: u32;
    var local_57: u32;
    var local_58: f32;
    var local_59: u32;
    var local_60: u32;
    var local_61: u32;
    var local_62: u32;
    var local_63: u32;
    var local_64: u32;
    var local_65: u32;
    var local_66: u32;
    var local_67: u32;
    var local_68: f32;
    var local_69: f32;
    var local_70: u32;
    var local_71: u32;
    var local_72: u32;
    var local_73: u32;
    var local_74: u32;
    var local_75: u32;
    var local_76: f32;
    var local_77: f32;
    var local_78: u32;
    var local_79: u32;
    var local_80: u32;
    var local_81: u32;
    var local_82: f32;
    var local_83: f32;
    var local_84: f32;
    var local_85: f32;
    var local_86: f32;
    var local_87: f32;
    var local_88: u32;
    var local_89: u32;
    var local_90: f32;
    var local_91: f32;
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

    local_54 = 0u;
    local_55 = 0u;
    local_56 = 0u;
    local_57 = 0u;
    let _e113 = build_cell_ids_array_args.cell_size;
    local_58 = _e113;
    let _e115 = build_cell_ids_array_args.num_particles;
    local_59 = _e115;
    let _e117 = gl_GlobalInvocationId_1[0u];
    local_60 = _e117;
    let _e118 = local_60;
    local_61 = _e118;
    let _e119 = local_61;
    let _e120 = local_59;
    local_62 = select(0u, 1u, (_e119 >= _e120));
    let _e123 = local_62;
    if (_e123 == 0u) {
        let _e125 = local_61;
        local_63 = (_e125 * 2u);
        let _e127 = local_63;
        local_64 = _e127;
        let _e128 = local_64;
        local_65 = _e128;
        let _e129 = local_65;
        local_66 = (_e129 * 4u);
        let _e131 = local_54;
        let _e132 = local_66;
        local_67 = (_e131 + _e132);
        let _e134 = local_67;
        let _e139 = positions.member[(_e134 >> bitcast<u32>(2u))];
        local_68 = _e139;
        let _e140 = local_68;
        local_69 = _e140;
        let _e141 = local_61;
        local_70 = (_e141 * 2u);
        let _e143 = local_70;
        local_71 = (_e143 + 1u);
        let _e145 = local_71;
        local_72 = _e145;
        let _e146 = local_72;
        local_73 = _e146;
        let _e147 = local_73;
        local_74 = (_e147 * 4u);
        let _e149 = local_54;
        let _e150 = local_74;
        local_75 = (_e149 + _e150);
        let _e152 = local_75;
        let _e157 = positions.member[(_e152 >> bitcast<u32>(2u))];
        local_76 = _e157;
        let _e158 = local_76;
        local_77 = _e158;
        let _e159 = local_61;
        local_78 = _e159;
        let _e160 = local_78;
        local_79 = _e160;
        let _e161 = local_79;
        local_80 = (_e161 * 4u);
        let _e163 = local_57;
        let _e164 = local_80;
        local_81 = (_e163 + _e164);
        let _e166 = local_81;
        let _e171 = radius.member[(_e166 >> bitcast<u32>(2u))];
        local_82 = _e171;
        let _e172 = local_82;
        local_83 = _e172;
        let _e173 = local_83;
        let _e174 = local_83;
        local_84 = (_e173 * _e174);
        let _e176 = local_84;
        local_85 = _e176;
        let _e177 = local_69;
        let _e178 = local_58;
        local_86 = (_e177 / _e178);
        let _e180 = local_86;
        local_87 = floor(_e180);
        let _e182 = local_87;
        let _e184 = select(_e182, 0f, (_e182 != _e182));
        local_88 = select(u32(clamp(_e184, -2147483600f, 2147483500f)), 2147483647u, (_e184 >= 2147483600f));
        let _e189 = local_88;
        local_89 = _e189;
        let _e190 = local_77;
        let _e191 = local_58;
        local_90 = (_e190 / _e191);
        let _e193 = local_90;
        local_91 = floor(_e193);
        let _e195 = local_91;
        let _e197 = select(_e195, 0f, (_e195 != _e195));
        local_92 = select(u32(clamp(_e197, -2147483600f, 2147483500f)), 2147483647u, (_e197 >= 2147483600f));
        let _e202 = local_92;
        local_93 = _e202;
        let _e203 = local_61;
        local_94 = (_e203 * 4u);
        let _e205 = local_94;
        local_95 = _e205;
        let _e206 = local_89;
        let _e207 = local_93;
        let _e208 = morton_encode(_e206, _e207);
        local_96 = _e208;
        let _e209 = local_95;
        local_97 = _e209;
        let _e210 = local_97;
        local_98 = _e210;
        let _e211 = local_98;
        local_99 = (_e211 * 4u);
        let _e213 = local_55;
        let _e214 = local_99;
        local_100 = (_e213 + _e214);
        let _e216 = local_100;
        let _e221 = local_96;
        cell_ids.member[(_e216 >> bitcast<u32>(2u))] = _e221;
        let _e222 = local_95;
        local_101 = _e222;
        let _e223 = local_101;
        local_102 = _e223;
        let _e224 = local_102;
        local_103 = (_e224 * 4u);
        let _e226 = local_56;
        let _e227 = local_103;
        local_104 = (_e226 + _e227);
        let _e229 = local_104;
        let _e234 = local_61;
        object_ids.member[(_e229 >> bitcast<u32>(2u))] = _e234;
        local_105 = 0u;
        local_106 = 4294967295u;
        loop {
            let _e235 = local_106;
            local_107 = select(0u, 1u, (bitcast<i32>(_e235) <= bitcast<i32>(1u)));
            let _e240 = local_107;
            if (_e240 == 0u) {
                break;
            } else {
                local_108 = 4294967295u;
                loop {
                    let _e242 = local_108;
                    local_109 = select(0u, 1u, (bitcast<i32>(_e242) <= bitcast<i32>(1u)));
                    let _e247 = local_109;
                    if (_e247 == 0u) {
                        break;
                    }
                    let _e249 = local_108;
                    local_110 = select(0u, 1u, (_e249 == 0u));
                    local_111 = 1u;
                    let _e252 = local_110;
                    if (_e252 == 0u) {
                        local_111 = 0u;
                    } else {
                        let _e254 = local_106;
                        local_112 = select(0u, 1u, (_e254 == 0u));
                        let _e257 = local_112;
                        if (_e257 == 0u) {
                            local_111 = 0u;
                        }
                    }
                    let _e259 = local_111;
                    if (_e259 == 0u) {
                        let _e261 = local_89;
                        let _e262 = local_108;
                        local_113 = (_e261 + _e262);
                        let _e264 = local_113;
                        local_114 = _e264;
                        let _e265 = local_93;
                        let _e266 = local_106;
                        local_115 = (_e265 + _e266);
                        let _e268 = local_115;
                        local_116 = _e268;
                        let _e269 = local_69;
                        let _e270 = local_77;
                        let _e271 = local_85;
                        let _e272 = local_114;
                        let _e273 = local_116;
                        let _e274 = local_58;
                        let _e275 = is_obj_in_cell(_e269, _e270, _e271, _e272, _e273, _e274);
                        local_117 = _e275;
                        let _e276 = local_117;
                        if (_e276 == 0u) {
                        } else {
                            let _e278 = local_105;
                            local_118 = (_e278 + 1u);
                            let _e280 = local_118;
                            local_105 = _e280;
                            let _e281 = local_95;
                            let _e282 = local_105;
                            local_119 = (_e281 + _e282);
                            let _e284 = local_119;
                            local_120 = _e284;
                            let _e285 = local_120;
                            local_121 = _e285;
                            let _e286 = local_114;
                            let _e287 = local_116;
                            let _e288 = morton_encode(_e286, _e287);
                            local_122 = _e288;
                            let _e289 = local_121;
                            local_123 = _e289;
                            let _e290 = local_123;
                            local_124 = (_e290 * 4u);
                            let _e292 = local_55;
                            let _e293 = local_124;
                            local_125 = (_e292 + _e293);
                            let _e295 = local_125;
                            let _e300 = local_122;
                            cell_ids.member[(_e295 >> bitcast<u32>(2u))] = _e300;
                            let _e301 = local_121;
                            local_126 = _e301;
                            let _e302 = local_126;
                            local_127 = (_e302 * 4u);
                            let _e304 = local_56;
                            let _e305 = local_127;
                            local_128 = (_e304 + _e305);
                            let _e307 = local_128;
                            let _e312 = local_61;
                            object_ids.member[(_e307 >> bitcast<u32>(2u))] = _e312;
                        }
                    }
                    let _e313 = local_108;
                    local_129 = _e313;
                    let _e314 = local_108;
                    local_130 = (_e314 + 1u);
                    let _e316 = local_130;
                    local_108 = _e316;
                    continue;
                }
                let _e317 = local_106;
                local_131 = _e317;
                let _e318 = local_106;
                local_132 = (_e318 + 1u);
                let _e320 = local_132;
                local_106 = _e320;
                continue;
            }
        }
        let _e321 = local_105;
        local_133 = (_e321 + 1u);
        let _e323 = local_133;
        local_134 = _e323;
        loop {
            let _e324 = local_134;
            local_135 = select(0u, 1u, (_e324 < 4u));
            let _e327 = local_135;
            if (_e327 == 0u) {
                break;
            } else {
                let _e329 = local_95;
                let _e330 = local_134;
                local_136 = (_e329 + _e330);
                let _e332 = local_136;
                local_137 = _e332;
                let _e333 = local_137;
                local_138 = _e333;
                let _e334 = local_138;
                local_139 = (_e334 * 4u);
                let _e336 = local_55;
                let _e337 = local_139;
                local_140 = (_e336 + _e337);
                let _e339 = local_140;
                cell_ids.member[(_e339 >> bitcast<u32>(2u))] = 4294967295u;
                let _e344 = local_134;
                local_141 = _e344;
                let _e345 = local_134;
                local_142 = (_e345 + 1u);
                let _e347 = local_142;
                local_134 = _e347;
                continue;
            }
        }
        return;
    } else {
        return;
    }
}

@compute @workgroup_size(64, 1, 1) 
fn build_cell_ids_array(@builtin(global_invocation_id) gl_GlobalInvocationId: vec3<u32>) {
    gl_GlobalInvocationId_1 = gl_GlobalInvocationId;
    build_cell_ids_array_1();
}
