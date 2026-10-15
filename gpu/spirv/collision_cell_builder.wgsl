struct chunk_obj_count_buffer {
    member: array<u32>,
}

struct uniform_data_buffer {
    member: array<u32>,
}

struct cell_ids_buffer {
    member: array<u32>,
}

struct collision_cells_buffer {
    member: array<u32>,
}

struct indirect_args_buffer {
    member: array<u32>,
}

@group(0) @binding(0) 
var<storage, read_write> chunk_obj_count: chunk_obj_count_buffer;
@group(0) @binding(3) 
var<storage, read_write> uniform_data: uniform_data_buffer;
@group(0) @binding(4) 
var<storage, read_write> cell_ids: cell_ids_buffer;
var<private> gl_GlobalInvocationId_2: vec3<u32>;
@group(0) @binding(0) 
var<storage, read_write> chunk_obj_count_1: chunk_obj_count_buffer;
@group(0) @binding(1) 
var<storage, read_write> collision_cells: collision_cells_buffer;
@group(0) @binding(2) 
var<storage, read_write> indirect_args: indirect_args_buffer;
@group(0) @binding(3) 
var<storage, read_write> uniform_data_1: uniform_data_buffer;
@group(0) @binding(4) 
var<storage, read_write> cell_ids_1: cell_ids_buffer;

fn get_total_chunks(param: u32) -> u32 {
    var local: u32;
    var local_1: u32;
    var local_2: u32;
    var local_3: u32;

    local = param;
    let _e20 = local;
    local_1 = (_e20 + 4u);
    let _e22 = local_1;
    local_2 = (_e22 - 1u);
    let _e24 = local_2;
    local_3 = (_e24 / 4u);
    let _e26 = local_3;
    return _e26;
}

fn count_objects_for_each_chunk_1() {
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

    local_4 = 0u;
    local_5 = 0u;
    local_6 = 0u;
    let _e74 = gl_GlobalInvocationId_2[0u];
    local_7 = _e74;
    let _e75 = local_7;
    local_8 = _e75;
    local_9 = (1u * 4u);
    let _e77 = local_5;
    let _e78 = local_9;
    local_10 = (_e77 + _e78);
    let _e80 = local_10;
    let _e85 = uniform_data.member[(_e80 >> bitcast<u32>(2u))];
    local_11 = _e85;
    let _e86 = local_11;
    local_12 = _e86;
    let _e87 = local_12;
    let _e88 = get_total_chunks(_e87);
    local_13 = _e88;
    let _e89 = local_8;
    let _e90 = local_13;
    local_14 = select(0u, 1u, (_e89 >= _e90));
    let _e93 = local_14;
    if (_e93 == 0u) {
    } else {
        return;
    }
    let _e95 = local_8;
    local_15 = (_e95 * 4u);
    let _e97 = local_15;
    local_16 = _e97;
    local_17 = 4294967295u;
    let _e98 = local_16;
    local_18 = select(0u, 1u, (_e98 >= 1u));
    let _e101 = local_18;
    if (_e101 == 0u) {
    } else {
        let _e103 = local_16;
        local_19 = (_e103 - 1u);
        let _e105 = local_19;
        local_20 = _e105;
        let _e106 = local_20;
        local_21 = _e106;
        let _e107 = local_21;
        local_22 = (_e107 * 4u);
        let _e109 = local_6;
        let _e110 = local_22;
        local_23 = (_e109 + _e110);
        let _e112 = local_23;
        let _e117 = cell_ids.member[(_e112 >> bitcast<u32>(2u))];
        local_24 = _e117;
        let _e118 = local_24;
        local_17 = _e118;
    }
    local_25 = 0u;
    local_26 = 4294967295u;
    local_27 = 0u;
    let _e119 = local_16;
    local_28 = (_e119 + 4u);
    let _e121 = local_28;
    local_29 = _e121;
    let _e122 = local_16;
    local_30 = _e122;
    loop {
        let _e123 = local_30;
        let _e124 = local_12;
        local_31 = select(0u, 1u, (_e123 < _e124));
        let _e127 = local_31;
        if (_e127 == 0u) {
            break;
        }
        let _e129 = local_30;
        local_32 = _e129;
        let _e130 = local_32;
        local_33 = _e130;
        let _e131 = local_33;
        local_34 = (_e131 * 4u);
        let _e133 = local_6;
        let _e134 = local_34;
        local_35 = (_e133 + _e134);
        let _e136 = local_35;
        let _e141 = cell_ids.member[(_e136 >> bitcast<u32>(2u))];
        local_36 = _e141;
        let _e142 = local_36;
        local_37 = _e142;
        let _e143 = local_30;
        let _e144 = local_29;
        local_38 = select(0u, 1u, (_e143 >= _e144));
        let _e147 = local_38;
        local_39 = select(0u, 1u, (_e147 != 0u));
        let _e150 = local_37;
        local_40 = select(0u, 1u, (_e150 == 4294967295u));
        let _e153 = local_40;
        local_41 = select(0u, 1u, (_e153 != 0u));
        let _e156 = local_37;
        let _e157 = local_17;
        local_42 = select(0u, 1u, (_e156 != _e157));
        let _e160 = local_42;
        local_43 = select(0u, 1u, (_e160 != 0u));
        local_44 = 1u;
        let _e163 = local_43;
        if (_e163 == 0u) {
            local_44 = 0u;
        } else {
            let _e165 = local_39;
            if (_e165 == 0u) {
                local_44 = 0u;
            }
        }
        local_45 = 0u;
        let _e167 = local_44;
        if (_e167 != 0u) {
            local_45 = 1u;
        } else {
            let _e169 = local_41;
            if (_e169 != 0u) {
                local_45 = 1u;
            }
        }
        local_46 = 0u;
        let _e171 = local_45;
        if (_e171 != 0u) {
            local_46 = 1u;
        } else {
            let _e173 = local_27;
            local_47 = select(0u, 1u, (_e173 == 0u));
            local_48 = 1u;
            let _e176 = local_47;
            if (_e176 == 0u) {
                local_48 = 0u;
            } else {
                let _e178 = local_39;
                if (_e178 == 0u) {
                    local_48 = 0u;
                }
            }
            local_49 = 1u;
            let _e180 = local_48;
            if (_e180 == 0u) {
                local_49 = 0u;
            } else {
                local_50 = 1u;
                let _e182 = local_43;
                if (_e182 == 0u) {
                } else {
                    local_50 = 0u;
                }
                let _e184 = local_50;
                if (_e184 == 0u) {
                    local_49 = 0u;
                }
            }
            let _e186 = local_49;
            if (_e186 != 0u) {
                local_46 = 1u;
            }
        }
        let _e188 = local_46;
        if (_e188 == 0u) {
        } else {
            break;
        }
        let _e190 = local_26;
        let _e191 = local_37;
        local_51 = select(0u, 1u, (_e190 == _e191));
        let _e194 = local_51;
        local_52 = select(0u, 1u, (_e194 != 0u));
        let _e197 = local_52;
        if (_e197 == 0u) {
        } else {
            let _e199 = local_27;
            local_53 = select(0u, 1u, (_e199 == 1u));
            let _e202 = local_53;
            if (_e202 == 0u) {
            } else {
                let _e204 = local_25;
                local_54 = (_e204 + 1u);
                let _e206 = local_54;
                local_25 = _e206;
            }
            let _e207 = local_27;
            local_55 = (_e207 + 1u);
            let _e209 = local_55;
            local_27 = _e209;
        }
        let _e210 = local_37;
        let _e211 = local_17;
        local_56 = select(0u, 1u, (_e210 != _e211));
        let _e214 = local_56;
        if (_e214 == 0u) {
        } else {
            local_27 = 1u;
            let _e216 = local_37;
            local_26 = _e216;
        }
        let _e217 = local_37;
        local_17 = _e217;
        let _e218 = local_30;
        local_57 = (_e218 + 1u);
        let _e220 = local_57;
        local_30 = _e220;
        continue;
    }
    let _e221 = local_8;
    local_58 = _e221;
    let _e222 = local_58;
    local_59 = _e222;
    let _e223 = local_59;
    local_60 = (_e223 * 4u);
    let _e225 = local_4;
    let _e226 = local_60;
    local_61 = (_e225 + _e226);
    let _e228 = local_61;
    let _e233 = local_25;
    chunk_obj_count.member[(_e228 >> bitcast<u32>(2u))] = _e233;
    return;
}

fn build_collision_cells_array_1() {
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

    local_62 = 0u;
    local_63 = 0u;
    local_64 = 0u;
    local_65 = 0u;
    local_66 = 0u;
    local_67 = (1u * 4u);
    let _e117 = local_65;
    let _e118 = local_67;
    local_68 = (_e117 + _e118);
    let _e120 = local_68;
    let _e125 = uniform_data_1.member[(_e120 >> bitcast<u32>(2u))];
    local_69 = _e125;
    let _e126 = local_69;
    local_70 = _e126;
    let _e128 = gl_GlobalInvocationId_2[0u];
    local_71 = _e128;
    let _e129 = local_71;
    local_72 = _e129;
    let _e130 = local_72;
    local_73 = select(0u, 1u, (_e130 == 0u));
    let _e133 = local_73;
    if (_e133 == 0u) {
    } else {
        local_74 = (0u * 4u);
        let _e136 = local_65;
        let _e137 = local_74;
        local_75 = (_e136 + _e137);
        let _e139 = local_75;
        let _e144 = uniform_data_1.member[(_e139 >> bitcast<u32>(2u))];
        local_76 = _e144;
        let _e145 = local_76;
        local_77 = (_e145 - 1u);
        let _e147 = local_77;
        local_78 = _e147;
        let _e148 = local_78;
        local_79 = _e148;
        let _e149 = local_79;
        local_80 = (_e149 * 4u);
        let _e151 = local_62;
        let _e152 = local_80;
        local_81 = (_e151 + _e152);
        let _e154 = local_81;
        let _e159 = chunk_obj_count_1.member[(_e154 >> bitcast<u32>(2u))];
        local_82 = _e159;
        let _e160 = local_82;
        local_83 = _e160;
        let _e161 = local_83;
        local_84 = (_e161 + 64u);
        let _e163 = local_84;
        local_85 = (_e163 - 1u);
        let _e165 = local_85;
        local_86 = (_e165 / 64u);
        let _e167 = local_86;
        local_87 = _e167;
        local_88 = (0u * 4u);
        let _e169 = local_64;
        let _e170 = local_88;
        local_89 = (_e169 + _e170);
        let _e172 = local_89;
        let _e177 = local_87;
        indirect_args.member[(_e172 >> bitcast<u32>(2u))] = _e177;
        local_90 = (1u * 4u);
        let _e179 = local_64;
        let _e180 = local_90;
        local_91 = (_e179 + _e180);
        let _e182 = local_91;
        indirect_args.member[(_e182 >> bitcast<u32>(2u))] = 1u;
        local_92 = (2u * 4u);
        let _e188 = local_64;
        let _e189 = local_92;
        local_93 = (_e188 + _e189);
        let _e191 = local_93;
        indirect_args.member[(_e191 >> bitcast<u32>(2u))] = 1u;
    }
    let _e196 = local_70;
    let _e197 = get_total_chunks(_e196);
    local_94 = _e197;
    let _e198 = local_72;
    let _e199 = local_94;
    local_95 = select(0u, 1u, (_e198 >= _e199));
    let _e202 = local_95;
    if (_e202 == 0u) {
    } else {
        return;
    }
    local_96 = 0u;
    let _e204 = local_72;
    local_97 = select(0u, 1u, (_e204 >= 1u));
    let _e207 = local_97;
    if (_e207 == 0u) {
    } else {
        let _e209 = local_72;
        local_98 = (_e209 - 1u);
        let _e211 = local_98;
        local_99 = _e211;
        let _e212 = local_99;
        local_100 = _e212;
        let _e213 = local_100;
        local_101 = (_e213 * 4u);
        let _e215 = local_62;
        let _e216 = local_101;
        local_102 = (_e215 + _e216);
        let _e218 = local_102;
        let _e223 = chunk_obj_count_1.member[(_e218 >> bitcast<u32>(2u))];
        local_103 = _e223;
        let _e224 = local_103;
        local_96 = _e224;
    }
    let _e225 = local_72;
    local_104 = _e225;
    let _e226 = local_104;
    local_105 = _e226;
    let _e227 = local_105;
    local_106 = (_e227 * 4u);
    let _e229 = local_62;
    let _e230 = local_106;
    local_107 = (_e229 + _e230);
    let _e232 = local_107;
    let _e237 = chunk_obj_count_1.member[(_e232 >> bitcast<u32>(2u))];
    local_108 = _e237;
    let _e238 = local_108;
    local_109 = _e238;
    let _e239 = local_109;
    let _e240 = local_96;
    local_110 = (_e239 - _e240);
    let _e242 = local_110;
    local_111 = _e242;
    let _e243 = local_111;
    local_112 = select(0u, 1u, (_e243 == 0u));
    let _e246 = local_112;
    if (_e246 == 0u) {
    } else {
        return;
    }
    let _e248 = local_72;
    local_113 = (_e248 * 4u);
    let _e250 = local_113;
    local_114 = _e250;
    local_115 = 4294967295u;
    let _e251 = local_114;
    local_116 = select(0u, 1u, (_e251 >= 1u));
    let _e254 = local_116;
    if (_e254 == 0u) {
    } else {
        let _e256 = local_114;
        local_117 = (_e256 - 1u);
        let _e258 = local_117;
        local_118 = _e258;
        let _e259 = local_118;
        local_119 = _e259;
        let _e260 = local_119;
        local_120 = (_e260 * 4u);
        let _e262 = local_66;
        let _e263 = local_120;
        local_121 = (_e262 + _e263);
        let _e265 = local_121;
        let _e270 = cell_ids_1.member[(_e265 >> bitcast<u32>(2u))];
        local_122 = _e270;
        let _e271 = local_122;
        local_115 = _e271;
    }
    local_123 = 4294967295u;
    local_124 = 0u;
    let _e272 = local_114;
    local_125 = (_e272 + 4u);
    let _e274 = local_125;
    local_126 = _e274;
    let _e275 = local_96;
    local_127 = _e275;
    let _e276 = local_114;
    local_128 = _e276;
    loop {
        let _e277 = local_128;
        let _e278 = local_70;
        local_129 = select(0u, 1u, (_e277 < _e278));
        local_130 = 1u;
        let _e281 = local_129;
        if (_e281 == 0u) {
            local_130 = 0u;
        } else {
            let _e283 = local_127;
            let _e284 = local_109;
            local_131 = select(0u, 1u, (_e283 != _e284));
            let _e287 = local_131;
            if (_e287 == 0u) {
                local_130 = 0u;
            }
        }
        let _e289 = local_130;
        if (_e289 == 0u) {
            break;
        }
        let _e291 = local_128;
        local_132 = _e291;
        let _e292 = local_132;
        local_133 = _e292;
        let _e293 = local_133;
        local_134 = (_e293 * 4u);
        let _e295 = local_66;
        let _e296 = local_134;
        local_135 = (_e295 + _e296);
        let _e298 = local_135;
        let _e303 = cell_ids_1.member[(_e298 >> bitcast<u32>(2u))];
        local_136 = _e303;
        let _e304 = local_136;
        local_137 = _e304;
        let _e305 = local_128;
        let _e306 = local_126;
        local_138 = select(0u, 1u, (_e305 >= _e306));
        let _e309 = local_138;
        local_139 = select(0u, 1u, (_e309 != 0u));
        let _e312 = local_137;
        local_140 = select(0u, 1u, (_e312 == 4294967295u));
        let _e315 = local_140;
        local_141 = select(0u, 1u, (_e315 != 0u));
        let _e318 = local_137;
        let _e319 = local_115;
        local_142 = select(0u, 1u, (_e318 != _e319));
        let _e322 = local_142;
        local_143 = select(0u, 1u, (_e322 != 0u));
        local_144 = 1u;
        let _e325 = local_143;
        if (_e325 == 0u) {
            local_144 = 0u;
        } else {
            let _e327 = local_139;
            if (_e327 == 0u) {
                local_144 = 0u;
            }
        }
        local_145 = 0u;
        let _e329 = local_144;
        if (_e329 != 0u) {
            local_145 = 1u;
        } else {
            let _e331 = local_141;
            if (_e331 != 0u) {
                local_145 = 1u;
            }
        }
        local_146 = 0u;
        let _e333 = local_145;
        if (_e333 != 0u) {
            local_146 = 1u;
        } else {
            let _e335 = local_124;
            local_147 = select(0u, 1u, (_e335 == 0u));
            local_148 = 1u;
            let _e338 = local_147;
            if (_e338 == 0u) {
                local_148 = 0u;
            } else {
                let _e340 = local_139;
                if (_e340 == 0u) {
                    local_148 = 0u;
                }
            }
            local_149 = 1u;
            let _e342 = local_148;
            if (_e342 == 0u) {
                local_149 = 0u;
            } else {
                local_150 = 1u;
                let _e344 = local_143;
                if (_e344 == 0u) {
                } else {
                    local_150 = 0u;
                }
                let _e346 = local_150;
                if (_e346 == 0u) {
                    local_149 = 0u;
                }
            }
            let _e348 = local_149;
            if (_e348 != 0u) {
                local_146 = 1u;
            }
        }
        let _e350 = local_146;
        if (_e350 == 0u) {
        } else {
            break;
        }
        let _e352 = local_123;
        let _e353 = local_137;
        local_151 = select(0u, 1u, (_e352 == _e353));
        let _e356 = local_151;
        local_152 = select(0u, 1u, (_e356 != 0u));
        let _e359 = local_152;
        if (_e359 == 0u) {
        } else {
            let _e361 = local_124;
            local_153 = select(0u, 1u, (_e361 == 1u));
            let _e364 = local_153;
            if (_e364 == 0u) {
            } else {
                let _e366 = local_128;
                local_154 = (_e366 - 1u);
                let _e368 = local_127;
                local_155 = _e368;
                let _e369 = local_155;
                local_156 = _e369;
                let _e370 = local_156;
                local_157 = (_e370 * 4u);
                let _e372 = local_63;
                let _e373 = local_157;
                local_158 = (_e372 + _e373);
                let _e375 = local_158;
                let _e380 = local_154;
                collision_cells.member[(_e375 >> bitcast<u32>(2u))] = _e380;
                let _e381 = local_127;
                local_159 = (_e381 + 1u);
                let _e383 = local_159;
                local_127 = _e383;
            }
            let _e384 = local_124;
            local_160 = (_e384 + 1u);
            let _e386 = local_160;
            local_124 = _e386;
        }
        let _e387 = local_137;
        let _e388 = local_115;
        local_161 = select(0u, 1u, (_e387 != _e388));
        let _e391 = local_161;
        if (_e391 == 0u) {
        } else {
            local_124 = 1u;
            let _e393 = local_137;
            local_123 = _e393;
        }
        let _e394 = local_137;
        local_115 = _e394;
        let _e395 = local_128;
        local_162 = (_e395 + 1u);
        let _e397 = local_162;
        local_128 = _e397;
        continue;
    }
    return;
}

@compute @workgroup_size(64, 1, 1) 
fn count_objects_for_each_chunk(@builtin(global_invocation_id) gl_GlobalInvocationId: vec3<u32>) {
    gl_GlobalInvocationId_2 = gl_GlobalInvocationId;
    count_objects_for_each_chunk_1();
}

@compute @workgroup_size(64, 1, 1) 
fn build_collision_cells_array(@builtin(global_invocation_id) gl_GlobalInvocationId_1: vec3<u32>) {
    gl_GlobalInvocationId_2 = gl_GlobalInvocationId_1;
    build_collision_cells_array_1();
}
