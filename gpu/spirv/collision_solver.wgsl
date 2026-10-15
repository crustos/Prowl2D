struct chunk_obj_count_buffer {
    member: array<u32>,
}

struct collision_cells_buffer {
    member: array<u32>,
}

struct cell_ids_buffer {
    member: array<u32>,
}

struct object_ids_buffer {
    member: array<u32>,
}

struct positions_buffer {
    member: array<f32>,
}

struct radius_buffer {
    member: array<f32>,
}

struct uniform_data_buffer {
    member: array<u32>,
}

struct solve_collisions_push {
    current_cell_color: u32,
}

@group(0) @binding(0) 
var<storage, read_write> chunk_obj_count: chunk_obj_count_buffer;
@group(0) @binding(1) 
var<storage, read_write> collision_cells: collision_cells_buffer;
@group(0) @binding(2) 
var<storage, read_write> cell_ids: cell_ids_buffer;
@group(0) @binding(3) 
var<storage, read_write> object_ids: object_ids_buffer;
@group(0) @binding(4) 
var<storage, read_write> positions: positions_buffer;
@group(0) @binding(5) 
var<storage, read_write> radius: radius_buffer;
@group(0) @binding(6) 
var<storage, read_write> uniform_data: uniform_data_buffer;
@group(0) @binding(30) 
var<uniform> solve_collisions_args: solve_collisions_push;
var<private> gl_GlobalInvocationId_1: vec3<u32>;

fn unsplit_by_bits(param: u32) -> u32 {
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

    local = param;
    let _e39 = local;
    local_1 = (_e39 & 1431655765u);
    let _e41 = local_1;
    local_2 = _e41;
    let _e42 = local_2;
    local_3 = (_e42 >> bitcast<u32>((1u & 31u)));
    let _e46 = local_2;
    let _e47 = local_3;
    local_4 = (_e46 | _e47);
    let _e49 = local_4;
    local_5 = (_e49 & 858993459u);
    let _e51 = local_5;
    local_2 = _e51;
    let _e52 = local_2;
    local_6 = (_e52 >> bitcast<u32>((2u & 31u)));
    let _e56 = local_2;
    let _e57 = local_6;
    local_7 = (_e56 | _e57);
    let _e59 = local_7;
    local_8 = (_e59 & 252645135u);
    let _e61 = local_8;
    local_2 = _e61;
    let _e62 = local_2;
    local_9 = (_e62 >> bitcast<u32>((4u & 31u)));
    let _e66 = local_2;
    let _e67 = local_9;
    local_10 = (_e66 | _e67);
    let _e69 = local_10;
    local_11 = (_e69 & 16711935u);
    let _e71 = local_11;
    local_2 = _e71;
    let _e72 = local_2;
    local_12 = (_e72 >> bitcast<u32>((8u & 31u)));
    let _e76 = local_2;
    let _e77 = local_12;
    local_13 = (_e76 | _e77);
    let _e79 = local_13;
    local_14 = (_e79 & 65535u);
    let _e81 = local_14;
    local_2 = _e81;
    let _e82 = local_2;
    return _e82;
}

fn get_cell_color(param_1: u32) -> u32 {
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

    local_15 = param_1;
    let _e35 = local_15;
    let _e36 = unsplit_by_bits(_e35);
    local_16 = _e36;
    let _e37 = local_16;
    local_17 = _e37;
    let _e38 = local_15;
    local_18 = (_e38 >> bitcast<u32>((1u & 31u)));
    let _e42 = local_18;
    let _e43 = unsplit_by_bits(_e42);
    local_19 = _e43;
    let _e44 = local_19;
    local_20 = _e44;
    let _e45 = local_17;
    local_21 = (_e45 % 2u);
    let _e47 = local_21;
    local_22 = (1u + _e47);
    let _e49 = local_20;
    local_23 = (_e49 % 2u);
    let _e51 = local_23;
    local_24 = (_e51 * 2u);
    let _e53 = local_22;
    let _e54 = local_24;
    local_25 = (_e53 + _e54);
    let _e56 = local_25;
    return _e56;
}

fn solve_collisions_1() {
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
    var local_101: f32;
    var local_102: f32;
    var local_103: u32;
    var local_104: u32;
    var local_105: u32;
    var local_106: u32;
    var local_107: u32;
    var local_108: f32;
    var local_109: f32;
    var local_110: u32;
    var local_111: u32;
    var local_112: u32;
    var local_113: u32;
    var local_114: f32;
    var local_115: f32;
    var local_116: u32;
    var local_117: u32;
    var local_118: u32;
    var local_119: u32;
    var local_120: u32;
    var local_121: f32;
    var local_122: f32;
    var local_123: u32;
    var local_124: u32;
    var local_125: u32;
    var local_126: f32;
    var local_127: f32;
    var local_128: u32;
    var local_129: u32;
    var local_130: u32;
    var local_131: f32;
    var local_132: f32;
    var local_133: f32;
    var local_134: f32;
    var local_135: f32;
    var local_136: f32;
    var local_137: f32;
    var local_138: f32;
    var local_139: f32;
    var local_140: f32;
    var local_141: f32;
    var local_142: f32;
    var local_143: f32;
    var local_144: f32;
    var local_145: f32;
    var local_146: u32;
    var local_147: u32;
    var local_148: f32;
    var local_149: u32;
    var local_150: f32;
    var local_151: f32;
    var local_152: f32;
    var local_153: f32;
    var local_154: f32;
    var local_155: f32;
    var local_156: f32;
    var local_157: f32;
    var local_158: f32;
    var local_159: f32;
    var local_160: f32;
    var local_161: f32;
    var local_162: f32;
    var local_163: f32;
    var local_164: f32;
    var local_165: f32;
    var local_166: f32;
    var local_167: f32;
    var local_168: f32;
    var local_169: f32;
    var local_170: f32;
    var local_171: f32;
    var local_172: f32;
    var local_173: f32;
    var local_174: f32;
    var local_175: f32;
    var local_176: u32;
    var local_177: u32;
    var local_178: u32;
    var local_179: u32;
    var local_180: f32;
    var local_181: f32;
    var local_182: u32;
    var local_183: u32;
    var local_184: u32;
    var local_185: u32;
    var local_186: u32;
    var local_187: f32;
    var local_188: f32;
    var local_189: u32;
    var local_190: u32;
    var local_191: u32;
    var local_192: u32;
    var local_193: f32;
    var local_194: f32;
    var local_195: u32;
    var local_196: u32;
    var local_197: u32;
    var local_198: u32;
    var local_199: u32;
    var local_200: u32;
    var local_201: u32;

    local_26 = 0u;
    local_27 = 0u;
    local_28 = 0u;
    local_29 = 0u;
    local_30 = 0u;
    local_31 = 0u;
    local_32 = 0u;
    let _e200 = solve_collisions_args.current_cell_color;
    local_33 = _e200;
    let _e202 = gl_GlobalInvocationId_1[0u];
    local_34 = _e202;
    let _e203 = local_34;
    local_35 = _e203;
    local_36 = (0u * 4u);
    let _e205 = local_32;
    let _e206 = local_36;
    local_37 = (_e205 + _e206);
    let _e208 = local_37;
    let _e213 = uniform_data.member[(_e208 >> bitcast<u32>(2u))];
    local_38 = _e213;
    let _e214 = local_38;
    local_39 = _e214;
    local_40 = (1u * 4u);
    let _e216 = local_32;
    let _e217 = local_40;
    local_41 = (_e216 + _e217);
    let _e219 = local_41;
    let _e224 = uniform_data.member[(_e219 >> bitcast<u32>(2u))];
    local_42 = _e224;
    let _e225 = local_42;
    local_43 = _e225;
    let _e226 = local_39;
    local_44 = (_e226 - 1u);
    let _e228 = local_44;
    local_45 = _e228;
    let _e229 = local_45;
    local_46 = _e229;
    let _e230 = local_46;
    local_47 = (_e230 * 4u);
    let _e232 = local_26;
    let _e233 = local_47;
    local_48 = (_e232 + _e233);
    let _e235 = local_48;
    let _e240 = chunk_obj_count.member[(_e235 >> bitcast<u32>(2u))];
    local_49 = _e240;
    let _e241 = local_49;
    local_50 = _e241;
    let _e242 = local_35;
    let _e243 = local_50;
    local_51 = select(0u, 1u, (_e242 >= _e243));
    let _e246 = local_51;
    if (_e246 == 0u) {
        let _e248 = local_35;
        local_52 = _e248;
        let _e249 = local_52;
        local_53 = _e249;
        let _e250 = local_53;
        local_54 = (_e250 * 4u);
        let _e252 = local_27;
        let _e253 = local_54;
        local_55 = (_e252 + _e253);
        let _e255 = local_55;
        let _e260 = collision_cells.member[(_e255 >> bitcast<u32>(2u))];
        local_56 = _e260;
        let _e261 = local_56;
        local_57 = _e261;
        let _e262 = local_57;
        local_58 = _e262;
        let _e263 = local_58;
        local_59 = _e263;
        let _e264 = local_59;
        local_60 = (_e264 * 4u);
        let _e266 = local_28;
        let _e267 = local_60;
        local_61 = (_e266 + _e267);
        let _e269 = local_61;
        let _e274 = cell_ids.member[(_e269 >> bitcast<u32>(2u))];
        local_62 = _e274;
        let _e275 = local_62;
        local_63 = _e275;
        let _e276 = local_63;
        let _e277 = get_cell_color(_e276);
        local_64 = _e277;
        let _e278 = local_64;
        let _e279 = local_33;
        local_65 = select(0u, 1u, (_e278 != _e279));
        let _e282 = local_65;
        if (_e282 == 0u) {
            let _e284 = local_57;
            local_66 = _e284;
            loop {
                let _e285 = local_66;
                let _e286 = local_43;
                local_67 = select(0u, 1u, (_e285 < _e286));
                let _e289 = local_67;
                if (_e289 == 0u) {
                    break;
                } else {
                    let _e291 = local_66;
                    local_68 = _e291;
                    let _e292 = local_68;
                    local_69 = _e292;
                    let _e293 = local_69;
                    local_70 = (_e293 * 4u);
                    let _e295 = local_28;
                    let _e296 = local_70;
                    local_71 = (_e295 + _e296);
                    let _e298 = local_71;
                    let _e303 = cell_ids.member[(_e298 >> bitcast<u32>(2u))];
                    local_72 = _e303;
                    let _e304 = local_72;
                    let _e305 = local_63;
                    local_73 = select(0u, 1u, (_e304 != _e305));
                    let _e308 = local_73;
                    if (_e308 == 0u) {
                        let _e310 = local_66;
                        local_74 = _e310;
                        let _e311 = local_74;
                        local_75 = _e311;
                        let _e312 = local_75;
                        local_76 = (_e312 * 4u);
                        let _e314 = local_29;
                        let _e315 = local_76;
                        local_77 = (_e314 + _e315);
                        let _e317 = local_77;
                        let _e322 = object_ids.member[(_e317 >> bitcast<u32>(2u))];
                        local_78 = _e322;
                        let _e323 = local_78;
                        local_79 = _e323;
                        let _e324 = local_79;
                        local_80 = _e324;
                        let _e325 = local_66;
                        local_81 = (_e325 + 1u);
                        let _e327 = local_81;
                        local_82 = _e327;
                        loop {
                            let _e328 = local_82;
                            let _e329 = local_43;
                            local_83 = select(0u, 1u, (_e328 < _e329));
                            let _e332 = local_83;
                            if (_e332 == 0u) {
                                let _e334 = local_66;
                                local_201 = (_e334 + 1u);
                                let _e336 = local_201;
                                local_66 = _e336;
                                break;
                            }
                            let _e337 = local_82;
                            local_84 = _e337;
                            let _e338 = local_84;
                            local_85 = _e338;
                            let _e339 = local_85;
                            local_86 = (_e339 * 4u);
                            let _e341 = local_28;
                            let _e342 = local_86;
                            local_87 = (_e341 + _e342);
                            let _e344 = local_87;
                            let _e349 = cell_ids.member[(_e344 >> bitcast<u32>(2u))];
                            local_88 = _e349;
                            let _e350 = local_88;
                            let _e351 = local_63;
                            local_89 = select(0u, 1u, (_e350 != _e351));
                            let _e354 = local_89;
                            if (_e354 == 0u) {
                            } else {
                                let _e356 = local_66;
                                local_201 = (_e356 + 1u);
                                let _e358 = local_201;
                                local_66 = _e358;
                                break;
                            }
                            let _e359 = local_82;
                            local_90 = _e359;
                            let _e360 = local_90;
                            local_91 = _e360;
                            let _e361 = local_91;
                            local_92 = (_e361 * 4u);
                            let _e363 = local_29;
                            let _e364 = local_92;
                            local_93 = (_e363 + _e364);
                            let _e366 = local_93;
                            let _e371 = object_ids.member[(_e366 >> bitcast<u32>(2u))];
                            local_94 = _e371;
                            let _e372 = local_94;
                            local_95 = _e372;
                            let _e373 = local_95;
                            local_96 = _e373;
                            let _e374 = local_80;
                            local_97 = (_e374 * 2u);
                            let _e376 = local_97;
                            local_98 = _e376;
                            let _e377 = local_98;
                            local_99 = (_e377 * 4u);
                            let _e379 = local_30;
                            let _e380 = local_99;
                            local_100 = (_e379 + _e380);
                            let _e382 = local_100;
                            let _e387 = positions.member[(_e382 >> bitcast<u32>(2u))];
                            local_101 = _e387;
                            let _e388 = local_101;
                            local_102 = _e388;
                            let _e389 = local_80;
                            local_103 = (_e389 * 2u);
                            let _e391 = local_103;
                            local_104 = (_e391 + 1u);
                            let _e393 = local_104;
                            local_105 = _e393;
                            let _e394 = local_105;
                            local_106 = (_e394 * 4u);
                            let _e396 = local_30;
                            let _e397 = local_106;
                            local_107 = (_e396 + _e397);
                            let _e399 = local_107;
                            let _e404 = positions.member[(_e399 >> bitcast<u32>(2u))];
                            local_108 = _e404;
                            let _e405 = local_108;
                            local_109 = _e405;
                            let _e406 = local_96;
                            local_110 = (_e406 * 2u);
                            let _e408 = local_110;
                            local_111 = _e408;
                            let _e409 = local_111;
                            local_112 = (_e409 * 4u);
                            let _e411 = local_30;
                            let _e412 = local_112;
                            local_113 = (_e411 + _e412);
                            let _e414 = local_113;
                            let _e419 = positions.member[(_e414 >> bitcast<u32>(2u))];
                            local_114 = _e419;
                            let _e420 = local_114;
                            local_115 = _e420;
                            let _e421 = local_96;
                            local_116 = (_e421 * 2u);
                            let _e423 = local_116;
                            local_117 = (_e423 + 1u);
                            let _e425 = local_117;
                            local_118 = _e425;
                            let _e426 = local_118;
                            local_119 = (_e426 * 4u);
                            let _e428 = local_30;
                            let _e429 = local_119;
                            local_120 = (_e428 + _e429);
                            let _e431 = local_120;
                            let _e436 = positions.member[(_e431 >> bitcast<u32>(2u))];
                            local_121 = _e436;
                            let _e437 = local_121;
                            local_122 = _e437;
                            let _e438 = local_80;
                            local_123 = _e438;
                            let _e439 = local_123;
                            local_124 = (_e439 * 4u);
                            let _e441 = local_31;
                            let _e442 = local_124;
                            local_125 = (_e441 + _e442);
                            let _e444 = local_125;
                            let _e449 = radius.member[(_e444 >> bitcast<u32>(2u))];
                            local_126 = _e449;
                            let _e450 = local_126;
                            local_127 = _e450;
                            let _e451 = local_96;
                            local_128 = _e451;
                            let _e452 = local_128;
                            local_129 = (_e452 * 4u);
                            let _e454 = local_31;
                            let _e455 = local_129;
                            local_130 = (_e454 + _e455);
                            let _e457 = local_130;
                            let _e462 = radius.member[(_e457 >> bitcast<u32>(2u))];
                            local_131 = _e462;
                            let _e463 = local_131;
                            local_132 = _e463;
                            let _e464 = local_102;
                            let _e465 = local_115;
                            local_133 = (_e464 - _e465);
                            let _e467 = local_133;
                            local_134 = _e467;
                            let _e468 = local_109;
                            let _e469 = local_122;
                            local_135 = (_e468 - _e469);
                            let _e471 = local_135;
                            local_136 = _e471;
                            let _e472 = local_134;
                            let _e473 = local_134;
                            local_137 = (_e472 * _e473);
                            let _e475 = local_136;
                            let _e476 = local_136;
                            local_138 = (_e475 * _e476);
                            let _e478 = local_137;
                            let _e479 = local_138;
                            local_139 = (_e478 + _e479);
                            let _e481 = local_139;
                            local_140 = sqrt(_e481);
                            let _e483 = local_140;
                            local_141 = _e483;
                            let _e484 = local_127;
                            let _e485 = local_132;
                            local_142 = (_e484 + _e485);
                            let _e487 = local_142;
                            local_143 = _e487;
                            let _e488 = local_143;
                            let _e489 = local_143;
                            local_144 = (_e488 * _e489);
                            let _e491 = local_141;
                            let _e492 = local_141;
                            local_145 = (_e491 * _e492);
                            let _e494 = local_144;
                            let _e495 = local_145;
                            local_146 = select(0u, 1u, (_e494 > _e495));
                            local_147 = 1u;
                            let _e498 = local_146;
                            if (_e498 == 0u) {
                                local_147 = 0u;
                            } else {
                                local_148 = 0.0001f;
                                let _e500 = local_141;
                                let _e501 = local_148;
                                local_149 = select(0u, 1u, (_e500 > _e501));
                                let _e504 = local_149;
                                if (_e504 == 0u) {
                                    local_147 = 0u;
                                }
                            }
                            let _e506 = local_147;
                            if (_e506 == 0u) {
                            } else {
                                let _e508 = local_143;
                                let _e509 = local_141;
                                local_150 = (_e508 - _e509);
                                let _e511 = local_150;
                                local_151 = _e511;
                                let _e512 = local_134;
                                let _e513 = local_141;
                                local_152 = (_e512 / _e513);
                                let _e515 = local_152;
                                local_153 = _e515;
                                let _e516 = local_136;
                                let _e517 = local_141;
                                local_154 = (_e516 / _e517);
                                let _e519 = local_154;
                                local_155 = _e519;
                                let _e520 = local_153;
                                let _e521 = local_151;
                                local_156 = (_e520 * _e521);
                                local_157 = 0.6f;
                                let _e523 = local_156;
                                let _e524 = local_157;
                                local_158 = (_e523 * _e524);
                                let _e526 = local_158;
                                local_159 = _e526;
                                let _e527 = local_155;
                                let _e528 = local_151;
                                local_160 = (_e527 * _e528);
                                local_161 = 0.6f;
                                let _e530 = local_160;
                                let _e531 = local_161;
                                local_162 = (_e530 * _e531);
                                let _e533 = local_162;
                                local_163 = _e533;
                                let _e534 = local_127;
                                local_164 = (1f / _e534);
                                let _e536 = local_164;
                                local_165 = _e536;
                                let _e537 = local_132;
                                local_166 = (1f / _e537);
                                let _e539 = local_166;
                                local_167 = _e539;
                                let _e540 = local_165;
                                let _e541 = local_167;
                                local_168 = (_e540 + _e541);
                                let _e543 = local_165;
                                let _e544 = local_168;
                                local_169 = (_e543 / _e544);
                                let _e546 = local_169;
                                local_170 = _e546;
                                let _e547 = local_165;
                                let _e548 = local_167;
                                local_171 = (_e547 + _e548);
                                let _e550 = local_167;
                                let _e551 = local_171;
                                local_172 = (_e550 / _e551);
                                let _e553 = local_172;
                                local_173 = _e553;
                                let _e554 = local_159;
                                let _e555 = local_170;
                                local_174 = (_e554 * _e555);
                                let _e557 = local_102;
                                let _e558 = local_174;
                                local_175 = (_e557 + _e558);
                                let _e560 = local_80;
                                local_176 = (_e560 * 2u);
                                let _e562 = local_176;
                                local_177 = _e562;
                                let _e563 = local_177;
                                local_178 = (_e563 * 4u);
                                let _e565 = local_30;
                                let _e566 = local_178;
                                local_179 = (_e565 + _e566);
                                let _e568 = local_179;
                                let _e573 = local_175;
                                positions.member[(_e568 >> bitcast<u32>(2u))] = _e573;
                                let _e574 = local_163;
                                let _e575 = local_170;
                                local_180 = (_e574 * _e575);
                                let _e577 = local_109;
                                let _e578 = local_180;
                                local_181 = (_e577 + _e578);
                                let _e580 = local_80;
                                local_182 = (_e580 * 2u);
                                let _e582 = local_182;
                                local_183 = (_e582 + 1u);
                                let _e584 = local_183;
                                local_184 = _e584;
                                let _e585 = local_184;
                                local_185 = (_e585 * 4u);
                                let _e587 = local_30;
                                let _e588 = local_185;
                                local_186 = (_e587 + _e588);
                                let _e590 = local_186;
                                let _e595 = local_181;
                                positions.member[(_e590 >> bitcast<u32>(2u))] = _e595;
                                let _e596 = local_159;
                                let _e597 = local_173;
                                local_187 = (_e596 * _e597);
                                let _e599 = local_115;
                                let _e600 = local_187;
                                local_188 = (_e599 - _e600);
                                let _e602 = local_96;
                                local_189 = (_e602 * 2u);
                                let _e604 = local_189;
                                local_190 = _e604;
                                let _e605 = local_190;
                                local_191 = (_e605 * 4u);
                                let _e607 = local_30;
                                let _e608 = local_191;
                                local_192 = (_e607 + _e608);
                                let _e610 = local_192;
                                let _e615 = local_188;
                                positions.member[(_e610 >> bitcast<u32>(2u))] = _e615;
                                let _e616 = local_163;
                                let _e617 = local_173;
                                local_193 = (_e616 * _e617);
                                let _e619 = local_122;
                                let _e620 = local_193;
                                local_194 = (_e619 - _e620);
                                let _e622 = local_96;
                                local_195 = (_e622 * 2u);
                                let _e624 = local_195;
                                local_196 = (_e624 + 1u);
                                let _e626 = local_196;
                                local_197 = _e626;
                                let _e627 = local_197;
                                local_198 = (_e627 * 4u);
                                let _e629 = local_30;
                                let _e630 = local_198;
                                local_199 = (_e629 + _e630);
                                let _e632 = local_199;
                                let _e637 = local_194;
                                positions.member[(_e632 >> bitcast<u32>(2u))] = _e637;
                            }
                            let _e638 = local_82;
                            local_200 = (_e638 + 1u);
                            let _e640 = local_200;
                            local_82 = _e640;
                            continue;
                        }
                        continue;
                    } else {
                        break;
                    }
                }
            }
            return;
        } else {
            return;
        }
    } else {
        return;
    }
}

@compute @workgroup_size(64, 1, 1) 
fn solve_collisions(@builtin(global_invocation_id) gl_GlobalInvocationId: vec3<u32>) {
    gl_GlobalInvocationId_1 = gl_GlobalInvocationId;
    solve_collisions_1();
}
