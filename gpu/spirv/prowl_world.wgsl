struct positions_buffer {
    member: array<f32>,
}

struct previous_positions_buffer {
    member: array<f32>,
}

struct radius_buffer {
    member: array<f32>,
}

struct integrate_world_push {
    delta_time: f32,
    gravity_x: f32,
    gravity_y: f32,
    damping: f32,
    world_width: f32,
    world_height: f32,
    num_particles: u32,
}

struct tiles_buffer {
    member: array<u32>,
}

struct tile_collide_push {
    tiles_w: u32,
    tiles_h: u32,
    num_particles: u32,
}

@group(0) @binding(0) 
var<storage, read_write> positions: positions_buffer;
@group(0) @binding(1) 
var<storage, read_write> previous_positions: previous_positions_buffer;
@group(0) @binding(2) 
var<storage, read_write> radius: radius_buffer;
@group(0) @binding(30) 
var<uniform> integrate_world_args: integrate_world_push;
var<private> gl_GlobalInvocationId_2: vec3<u32>;
@group(0) @binding(0) 
var<storage, read_write> positions_1: positions_buffer;
@group(0) @binding(2) 
var<storage, read_write> radius_1: radius_buffer;
@group(0) @binding(5) 
var<storage, read_write> tiles: tiles_buffer;
@group(0) @binding(30) 
var<uniform> tile_collide_args: tile_collide_push;

fn integrate_world_1() {
    var local: u32;
    var local_1: u32;
    var local_2: u32;
    var local_3: f32;
    var local_4: f32;
    var local_5: f32;
    var local_6: f32;
    var local_7: f32;
    var local_8: f32;
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
    var local_19: f32;
    var local_20: f32;
    var local_21: u32;
    var local_22: u32;
    var local_23: u32;
    var local_24: u32;
    var local_25: f32;
    var local_26: f32;
    var local_27: u32;
    var local_28: u32;
    var local_29: u32;
    var local_30: f32;
    var local_31: f32;
    var local_32: f32;
    var local_33: f32;
    var local_34: u32;
    var local_35: u32;
    var local_36: u32;
    var local_37: u32;
    var local_38: f32;
    var local_39: f32;
    var local_40: f32;
    var local_41: f32;
    var local_42: f32;
    var local_43: f32;
    var local_44: f32;
    var local_45: f32;
    var local_46: f32;
    var local_47: f32;
    var local_48: f32;
    var local_49: f32;
    var local_50: f32;
    var local_51: f32;
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
    var local_63: f32;
    var local_64: f32;
    var local_65: f32;
    var local_66: f32;
    var local_67: f32;
    var local_68: f32;
    var local_69: f32;
    var local_70: f32;
    var local_71: u32;
    var local_72: u32;
    var local_73: u32;
    var local_74: u32;
    var local_75: u32;
    var local_76: u32;
    var local_77: u32;

    local = 0u;
    local_1 = 0u;
    local_2 = 0u;
    let _e103 = integrate_world_args.delta_time;
    local_3 = _e103;
    let _e105 = integrate_world_args.gravity_x;
    local_4 = _e105;
    let _e107 = integrate_world_args.gravity_y;
    local_5 = _e107;
    let _e109 = integrate_world_args.damping;
    local_6 = _e109;
    let _e111 = integrate_world_args.world_width;
    local_7 = _e111;
    let _e113 = integrate_world_args.world_height;
    local_8 = _e113;
    let _e115 = integrate_world_args.num_particles;
    local_9 = _e115;
    let _e117 = gl_GlobalInvocationId_2[0u];
    local_10 = _e117;
    let _e118 = local_10;
    local_11 = _e118;
    let _e119 = local_11;
    let _e120 = local_9;
    local_12 = select(0u, 1u, (_e119 >= _e120));
    let _e123 = local_12;
    if (_e123 == 0u) {
        let _e125 = local_11;
        local_13 = (_e125 * 2u);
        let _e127 = local_13;
        local_14 = _e127;
        let _e128 = local_14;
        local_15 = _e128;
        let _e129 = local_15;
        local_16 = _e129;
        let _e130 = local_16;
        local_17 = (_e130 * 4u);
        let _e132 = local;
        let _e133 = local_17;
        local_18 = (_e132 + _e133);
        let _e135 = local_18;
        let _e140 = positions.member[(_e135 >> bitcast<u32>(2u))];
        local_19 = _e140;
        let _e141 = local_19;
        local_20 = _e141;
        let _e142 = local_15;
        local_21 = (_e142 + 1u);
        let _e144 = local_21;
        local_22 = _e144;
        let _e145 = local_22;
        local_23 = (_e145 * 4u);
        let _e147 = local;
        let _e148 = local_23;
        local_24 = (_e147 + _e148);
        let _e150 = local_24;
        let _e155 = positions.member[(_e150 >> bitcast<u32>(2u))];
        local_25 = _e155;
        let _e156 = local_25;
        local_26 = _e156;
        let _e157 = local_15;
        local_27 = _e157;
        let _e158 = local_27;
        local_28 = (_e158 * 4u);
        let _e160 = local_1;
        let _e161 = local_28;
        local_29 = (_e160 + _e161);
        let _e163 = local_29;
        let _e168 = previous_positions.member[(_e163 >> bitcast<u32>(2u))];
        local_30 = _e168;
        let _e169 = local_20;
        let _e170 = local_30;
        local_31 = (_e169 - _e170);
        let _e172 = local_31;
        let _e173 = local_6;
        local_32 = (_e172 * _e173);
        let _e175 = local_32;
        local_33 = _e175;
        let _e176 = local_15;
        local_34 = (_e176 + 1u);
        let _e178 = local_34;
        local_35 = _e178;
        let _e179 = local_35;
        local_36 = (_e179 * 4u);
        let _e181 = local_1;
        let _e182 = local_36;
        local_37 = (_e181 + _e182);
        let _e184 = local_37;
        let _e189 = previous_positions.member[(_e184 >> bitcast<u32>(2u))];
        local_38 = _e189;
        let _e190 = local_26;
        let _e191 = local_38;
        local_39 = (_e190 - _e191);
        let _e193 = local_39;
        let _e194 = local_6;
        local_40 = (_e193 * _e194);
        let _e196 = local_40;
        local_41 = _e196;
        let _e197 = local_3;
        let _e198 = local_3;
        local_42 = (_e197 * _e198);
        let _e200 = local_42;
        local_43 = _e200;
        let _e201 = local_20;
        let _e202 = local_33;
        local_44 = (_e201 + _e202);
        let _e204 = local_4;
        let _e205 = local_43;
        local_45 = (_e204 * _e205);
        let _e207 = local_44;
        let _e208 = local_45;
        local_46 = (_e207 + _e208);
        let _e210 = local_46;
        local_47 = _e210;
        let _e211 = local_26;
        let _e212 = local_41;
        local_48 = (_e211 + _e212);
        let _e214 = local_5;
        let _e215 = local_43;
        local_49 = (_e214 * _e215);
        let _e217 = local_48;
        let _e218 = local_49;
        local_50 = (_e217 + _e218);
        let _e220 = local_50;
        local_51 = _e220;
        let _e221 = local_15;
        local_52 = _e221;
        let _e222 = local_52;
        local_53 = (_e222 * 4u);
        let _e224 = local_1;
        let _e225 = local_53;
        local_54 = (_e224 + _e225);
        let _e227 = local_54;
        let _e232 = local_20;
        previous_positions.member[(_e227 >> bitcast<u32>(2u))] = _e232;
        let _e233 = local_15;
        local_55 = (_e233 + 1u);
        let _e235 = local_55;
        local_56 = _e235;
        let _e236 = local_56;
        local_57 = (_e236 * 4u);
        let _e238 = local_1;
        let _e239 = local_57;
        local_58 = (_e238 + _e239);
        let _e241 = local_58;
        let _e246 = local_26;
        previous_positions.member[(_e241 >> bitcast<u32>(2u))] = _e246;
        let _e247 = local_11;
        local_59 = _e247;
        let _e248 = local_59;
        local_60 = _e248;
        let _e249 = local_60;
        local_61 = (_e249 * 4u);
        let _e251 = local_2;
        let _e252 = local_61;
        local_62 = (_e251 + _e252);
        let _e254 = local_62;
        let _e259 = radius.member[(_e254 >> bitcast<u32>(2u))];
        local_63 = _e259;
        let _e260 = local_63;
        local_64 = _e260;
        let _e261 = local_47;
        let _e262 = local_64;
        local_65 = max(_e261, _e262);
        let _e264 = local_7;
        let _e265 = local_64;
        local_66 = (_e264 - _e265);
        let _e267 = local_65;
        let _e268 = local_66;
        local_67 = min(_e267, _e268);
        let _e270 = local_67;
        local_47 = _e270;
        let _e271 = local_51;
        let _e272 = local_64;
        local_68 = max(_e271, _e272);
        let _e274 = local_8;
        let _e275 = local_64;
        local_69 = (_e274 - _e275);
        let _e277 = local_68;
        let _e278 = local_69;
        local_70 = min(_e277, _e278);
        let _e280 = local_70;
        local_51 = _e280;
        let _e281 = local_15;
        local_71 = _e281;
        let _e282 = local_71;
        local_72 = (_e282 * 4u);
        let _e284 = local;
        let _e285 = local_72;
        local_73 = (_e284 + _e285);
        let _e287 = local_73;
        let _e292 = local_47;
        positions.member[(_e287 >> bitcast<u32>(2u))] = _e292;
        let _e293 = local_15;
        local_74 = (_e293 + 1u);
        let _e295 = local_74;
        local_75 = _e295;
        let _e296 = local_75;
        local_76 = (_e296 * 4u);
        let _e298 = local;
        let _e299 = local_76;
        local_77 = (_e298 + _e299);
        let _e301 = local_77;
        let _e306 = local_51;
        positions.member[(_e301 >> bitcast<u32>(2u))] = _e306;
        return;
    } else {
        return;
    }
}

fn tile_index(param: u32, param_1: u32, param_2: u32, param_3: u32) -> u32 {
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

    local_78 = param;
    local_79 = param_1;
    local_80 = param_2;
    local_81 = param_3;
    let _e41 = local_80;
    local_82 = select(0u, 1u, (bitcast<i32>(_e41) < bitcast<i32>(0u)));
    local_83 = 0u;
    let _e46 = local_82;
    if (_e46 != 0u) {
        local_83 = 1u;
    } else {
        let _e48 = local_81;
        local_84 = select(0u, 1u, (bitcast<i32>(_e48) < bitcast<i32>(0u)));
        let _e53 = local_84;
        if (_e53 != 0u) {
            local_83 = 1u;
        }
    }
    local_85 = 0u;
    let _e55 = local_83;
    if (_e55 != 0u) {
        local_85 = 1u;
    } else {
        let _e57 = local_80;
        let _e58 = local_78;
        local_86 = select(0u, 1u, (bitcast<i32>(_e57) >= bitcast<i32>(_e58)));
        let _e63 = local_86;
        if (_e63 != 0u) {
            local_85 = 1u;
        }
    }
    local_87 = 0u;
    let _e65 = local_85;
    if (_e65 != 0u) {
        local_87 = 1u;
    } else {
        let _e67 = local_81;
        let _e68 = local_79;
        local_88 = select(0u, 1u, (bitcast<i32>(_e67) >= bitcast<i32>(_e68)));
        let _e73 = local_88;
        if (_e73 != 0u) {
            local_87 = 1u;
        }
    }
    let _e75 = local_87;
    if (_e75 == 0u) {
        let _e77 = local_81;
        let _e78 = local_78;
        local_89 = (_e77 * _e78);
        let _e80 = local_89;
        let _e81 = local_80;
        local_90 = (_e80 + _e81);
        let _e83 = local_90;
        return _e83;
    } else {
        return 4294967295u;
    }
}

fn tile_collide_1() {
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
    var local_111: f32;
    var local_112: f32;
    var local_113: u32;
    var local_114: u32;
    var local_115: u32;
    var local_116: f32;
    var local_117: f32;
    var local_118: u32;
    var local_119: u32;
    var local_120: u32;
    var local_121: u32;
    var local_122: f32;
    var local_123: f32;
    var local_124: f32;
    var local_125: f32;
    var local_126: u32;
    var local_127: u32;
    var local_128: f32;
    var local_129: f32;
    var local_130: u32;
    var local_131: u32;
    var local_132: f32;
    var local_133: f32;
    var local_134: u32;
    var local_135: u32;
    var local_136: f32;
    var local_137: f32;
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
    var local_177: f32;
    var local_178: u32;
    var local_179: f32;
    var local_180: f32;
    var local_181: f32;
    var local_182: f32;
    var local_183: f32;
    var local_184: f32;
    var local_185: f32;
    var local_186: f32;
    var local_187: f32;
    var local_188: f32;
    var local_189: f32;
    var local_190: f32;
    var local_191: f32;
    var local_192: f32;
    var local_193: f32;
    var local_194: f32;
    var local_195: f32;
    var local_196: f32;
    var local_197: f32;
    var local_198: u32;
    var local_199: u32;
    var local_200: u32;
    var local_201: u32;
    var local_202: u32;
    var local_203: u32;
    var local_204: u32;
    var local_205: u32;
    var local_206: u32;
    var local_207: u32;
    var local_208: u32;
    var local_209: u32;
    var local_210: u32;
    var local_211: u32;
    var local_212: u32;
    var local_213: u32;
    var local_214: u32;
    var local_215: u32;
    var local_216: u32;
    var local_217: u32;
    var local_218: u32;
    var local_219: u32;
    var local_220: u32;
    var local_221: u32;
    var local_222: u32;
    var local_223: u32;
    var local_224: u32;
    var local_225: u32;
    var local_226: u32;
    var local_227: u32;
    var local_228: u32;
    var local_229: u32;
    var local_230: u32;
    var local_231: u32;
    var local_232: u32;
    var local_233: u32;
    var local_234: u32;
    var local_235: u32;
    var local_236: u32;
    var local_237: u32;
    var local_238: f32;
    var local_239: f32;
    var local_240: f32;
    var local_241: u32;
    var local_242: f32;
    var local_243: f32;
    var local_244: u32;
    var local_245: f32;
    var local_246: u32;
    var local_247: f32;
    var local_248: f32;
    var local_249: u32;
    var local_250: f32;
    var local_251: f32;
    var local_252: f32;
    var local_253: u32;
    var local_254: u32;
    var local_255: u32;
    var local_256: u32;
    var local_257: u32;
    var local_258: u32;
    var local_259: u32;
    var local_260: u32;
    var local_261: u32;
    var local_262: u32;
    var local_263: u32;

    local_91 = 0u;
    local_92 = 0u;
    local_93 = 0u;
    let _e198 = tile_collide_args.tiles_w;
    local_94 = _e198;
    let _e200 = tile_collide_args.tiles_h;
    local_95 = _e200;
    let _e202 = tile_collide_args.num_particles;
    local_96 = _e202;
    let _e204 = gl_GlobalInvocationId_2[0u];
    local_97 = _e204;
    let _e205 = local_97;
    local_98 = _e205;
    let _e206 = local_98;
    let _e207 = local_96;
    local_99 = select(0u, 1u, (_e206 >= _e207));
    let _e210 = local_99;
    if (_e210 == 0u) {
        let _e212 = local_98;
        local_100 = (_e212 * 2u);
        let _e214 = local_100;
        local_101 = _e214;
        let _e215 = local_101;
        local_102 = _e215;
        let _e216 = local_94;
        local_103 = _e216;
        let _e217 = local_103;
        local_104 = _e217;
        let _e218 = local_95;
        local_105 = _e218;
        let _e219 = local_105;
        local_106 = _e219;
        let _e220 = local_98;
        local_107 = _e220;
        let _e221 = local_107;
        local_108 = _e221;
        let _e222 = local_108;
        local_109 = (_e222 * 4u);
        let _e224 = local_92;
        let _e225 = local_109;
        local_110 = (_e224 + _e225);
        let _e227 = local_110;
        let _e232 = radius_1.member[(_e227 >> bitcast<u32>(2u))];
        local_111 = _e232;
        let _e233 = local_111;
        local_112 = _e233;
        let _e234 = local_102;
        local_113 = _e234;
        let _e235 = local_113;
        local_114 = (_e235 * 4u);
        let _e237 = local_91;
        let _e238 = local_114;
        local_115 = (_e237 + _e238);
        let _e240 = local_115;
        let _e245 = positions_1.member[(_e240 >> bitcast<u32>(2u))];
        local_116 = _e245;
        let _e246 = local_116;
        local_117 = _e246;
        let _e247 = local_102;
        local_118 = (_e247 + 1u);
        let _e249 = local_118;
        local_119 = _e249;
        let _e250 = local_119;
        local_120 = (_e250 * 4u);
        let _e252 = local_91;
        let _e253 = local_120;
        local_121 = (_e252 + _e253);
        let _e255 = local_121;
        let _e260 = positions_1.member[(_e255 >> bitcast<u32>(2u))];
        local_122 = _e260;
        let _e261 = local_122;
        local_123 = _e261;
        let _e262 = local_117;
        let _e263 = local_112;
        local_124 = (_e262 - _e263);
        let _e265 = local_124;
        local_125 = floor(_e265);
        let _e267 = local_125;
        let _e269 = select(_e267, 0f, (_e267 != _e267));
        local_126 = select(u32(clamp(_e269, -2147483600f, 2147483500f)), 2147483647u, (_e269 >= 2147483600f));
        let _e274 = local_126;
        local_127 = _e274;
        let _e275 = local_117;
        let _e276 = local_112;
        local_128 = (_e275 + _e276);
        let _e278 = local_128;
        local_129 = floor(_e278);
        let _e280 = local_129;
        let _e282 = select(_e280, 0f, (_e280 != _e280));
        local_130 = select(u32(clamp(_e282, -2147483600f, 2147483500f)), 2147483647u, (_e282 >= 2147483600f));
        let _e287 = local_130;
        local_131 = _e287;
        let _e288 = local_123;
        let _e289 = local_112;
        local_132 = (_e288 - _e289);
        let _e291 = local_132;
        local_133 = floor(_e291);
        let _e293 = local_133;
        let _e295 = select(_e293, 0f, (_e293 != _e293));
        local_134 = select(u32(clamp(_e295, -2147483600f, 2147483500f)), 2147483647u, (_e295 >= 2147483600f));
        let _e300 = local_134;
        local_135 = _e300;
        let _e301 = local_123;
        let _e302 = local_112;
        local_136 = (_e301 + _e302);
        let _e304 = local_136;
        local_137 = floor(_e304);
        let _e306 = local_137;
        let _e308 = select(_e306, 0f, (_e306 != _e306));
        local_138 = select(u32(clamp(_e308, -2147483600f, 2147483500f)), 2147483647u, (_e308 >= 2147483600f));
        let _e313 = local_138;
        local_139 = _e313;
        let _e314 = local_139;
        local_140 = _e314;
        let _e315 = local_135;
        local_141 = _e315;
        loop {
            let _e316 = local_141;
            let _e317 = local_140;
            local_142 = select(0u, 1u, (bitcast<i32>(_e316) <= bitcast<i32>(_e317)));
            let _e322 = local_142;
            if (_e322 == 0u) {
                break;
            } else {
                let _e324 = local_131;
                local_143 = _e324;
                let _e325 = local_127;
                local_144 = _e325;
                loop {
                    let _e326 = local_144;
                    let _e327 = local_143;
                    local_145 = select(0u, 1u, (bitcast<i32>(_e326) <= bitcast<i32>(_e327)));
                    let _e332 = local_145;
                    if (_e332 == 0u) {
                        break;
                    }
                    let _e334 = local_104;
                    let _e335 = local_106;
                    let _e336 = local_144;
                    let _e337 = local_141;
                    let _e338 = tile_index(_e334, _e335, _e336, _e337);
                    local_146 = _e338;
                    let _e339 = local_146;
                    local_147 = _e339;
                    let _e340 = local_147;
                    local_148 = select(0u, 1u, (bitcast<i32>(_e340) >= bitcast<i32>(0u)));
                    local_149 = 1u;
                    let _e345 = local_148;
                    if (_e345 == 0u) {
                        local_149 = 0u;
                    } else {
                        let _e347 = local_147;
                        local_150 = _e347;
                        let _e348 = local_150;
                        local_151 = _e348;
                        let _e349 = local_151;
                        local_152 = (_e349 * 4u);
                        let _e351 = local_93;
                        let _e352 = local_152;
                        local_153 = (_e351 + _e352);
                        let _e354 = local_153;
                        let _e359 = tiles.member[(_e354 >> bitcast<u32>(2u))];
                        local_154 = _e359;
                        let _e360 = local_154;
                        local_155 = select(0u, 1u, (_e360 != 0u));
                        let _e363 = local_155;
                        if (_e363 == 0u) {
                            local_149 = 0u;
                        }
                    }
                    let _e365 = local_149;
                    if (_e365 == 0u) {
                    } else {
                        let _e367 = local_144;
                        local_156 = f32(_e367);
                        let _e369 = local_156;
                        local_157 = _e369;
                        let _e370 = local_141;
                        local_158 = f32(_e370);
                        let _e372 = local_158;
                        local_159 = _e372;
                        let _e373 = local_117;
                        let _e374 = local_157;
                        local_160 = max(_e373, _e374);
                        let _e376 = local_157;
                        local_161 = (_e376 + 1f);
                        let _e378 = local_160;
                        let _e379 = local_161;
                        local_162 = min(_e378, _e379);
                        let _e381 = local_162;
                        local_163 = _e381;
                        let _e382 = local_123;
                        let _e383 = local_159;
                        local_164 = max(_e382, _e383);
                        let _e385 = local_159;
                        local_165 = (_e385 + 1f);
                        let _e387 = local_164;
                        let _e388 = local_165;
                        local_166 = min(_e387, _e388);
                        let _e390 = local_166;
                        local_167 = _e390;
                        let _e391 = local_117;
                        let _e392 = local_163;
                        local_168 = (_e391 - _e392);
                        let _e394 = local_168;
                        local_169 = _e394;
                        let _e395 = local_123;
                        let _e396 = local_167;
                        local_170 = (_e395 - _e396);
                        let _e398 = local_170;
                        local_171 = _e398;
                        let _e399 = local_169;
                        let _e400 = local_169;
                        local_172 = (_e399 * _e400);
                        let _e402 = local_171;
                        let _e403 = local_171;
                        local_173 = (_e402 * _e403);
                        let _e405 = local_172;
                        let _e406 = local_173;
                        local_174 = (_e405 + _e406);
                        let _e408 = local_174;
                        local_175 = _e408;
                        let _e409 = local_175;
                        local_176 = select(0u, 1u, (_e409 > 0f));
                        let _e412 = local_176;
                        if (_e412 == 0u) {
                            let _e414 = local_117;
                            let _e415 = local_157;
                            local_188 = (_e414 - _e415);
                            let _e417 = local_188;
                            local_189 = _e417;
                            let _e418 = local_157;
                            local_190 = (_e418 + 1f);
                            let _e420 = local_190;
                            let _e421 = local_117;
                            local_191 = (_e420 - _e421);
                            let _e423 = local_191;
                            local_192 = _e423;
                            let _e424 = local_123;
                            let _e425 = local_159;
                            local_193 = (_e424 - _e425);
                            let _e427 = local_193;
                            local_194 = _e427;
                            let _e428 = local_159;
                            local_195 = (_e428 + 1f);
                            let _e430 = local_195;
                            let _e431 = local_123;
                            local_196 = (_e430 - _e431);
                            let _e433 = local_196;
                            local_197 = _e433;
                            let _e434 = local_144;
                            local_198 = (_e434 - 1u);
                            let _e436 = local_104;
                            let _e437 = local_106;
                            let _e438 = local_198;
                            let _e439 = local_141;
                            let _e440 = tile_index(_e436, _e437, _e438, _e439);
                            local_199 = _e440;
                            let _e441 = local_199;
                            local_200 = _e441;
                            let _e442 = local_144;
                            local_201 = (_e442 + 1u);
                            let _e444 = local_104;
                            let _e445 = local_106;
                            let _e446 = local_201;
                            let _e447 = local_141;
                            let _e448 = tile_index(_e444, _e445, _e446, _e447);
                            local_202 = _e448;
                            let _e449 = local_202;
                            local_203 = _e449;
                            let _e450 = local_141;
                            local_204 = (_e450 - 1u);
                            let _e452 = local_104;
                            let _e453 = local_106;
                            let _e454 = local_144;
                            let _e455 = local_204;
                            let _e456 = tile_index(_e452, _e453, _e454, _e455);
                            local_205 = _e456;
                            let _e457 = local_205;
                            local_206 = _e457;
                            let _e458 = local_141;
                            local_207 = (_e458 + 1u);
                            let _e460 = local_104;
                            let _e461 = local_106;
                            let _e462 = local_144;
                            let _e463 = local_207;
                            let _e464 = tile_index(_e460, _e461, _e462, _e463);
                            local_208 = _e464;
                            let _e465 = local_208;
                            local_209 = _e465;
                            let _e466 = local_200;
                            local_210 = select(0u, 1u, (bitcast<i32>(_e466) >= bitcast<i32>(0u)));
                            let _e471 = local_210;
                            if (_e471 == 0u) {
                            } else {
                                let _e473 = local_200;
                                local_211 = _e473;
                                let _e474 = local_211;
                                local_212 = _e474;
                                let _e475 = local_212;
                                local_213 = (_e475 * 4u);
                                let _e477 = local_93;
                                let _e478 = local_213;
                                local_214 = (_e477 + _e478);
                                let _e480 = local_214;
                                let _e485 = tiles.member[(_e480 >> bitcast<u32>(2u))];
                                local_215 = _e485;
                                let _e486 = local_215;
                                local_216 = select(0u, 1u, (_e486 != 0u));
                                let _e489 = local_216;
                                if (_e489 == 0u) {
                                } else {
                                    local_189 = 1000000000f;
                                }
                            }
                            let _e491 = local_203;
                            local_217 = select(0u, 1u, (bitcast<i32>(_e491) >= bitcast<i32>(0u)));
                            let _e496 = local_217;
                            if (_e496 == 0u) {
                            } else {
                                let _e498 = local_203;
                                local_218 = _e498;
                                let _e499 = local_218;
                                local_219 = _e499;
                                let _e500 = local_219;
                                local_220 = (_e500 * 4u);
                                let _e502 = local_93;
                                let _e503 = local_220;
                                local_221 = (_e502 + _e503);
                                let _e505 = local_221;
                                let _e510 = tiles.member[(_e505 >> bitcast<u32>(2u))];
                                local_222 = _e510;
                                let _e511 = local_222;
                                local_223 = select(0u, 1u, (_e511 != 0u));
                                let _e514 = local_223;
                                if (_e514 == 0u) {
                                } else {
                                    local_192 = 1000000000f;
                                }
                            }
                            let _e516 = local_206;
                            local_224 = select(0u, 1u, (bitcast<i32>(_e516) >= bitcast<i32>(0u)));
                            let _e521 = local_224;
                            if (_e521 == 0u) {
                            } else {
                                let _e523 = local_206;
                                local_225 = _e523;
                                let _e524 = local_225;
                                local_226 = _e524;
                                let _e525 = local_226;
                                local_227 = (_e525 * 4u);
                                let _e527 = local_93;
                                let _e528 = local_227;
                                local_228 = (_e527 + _e528);
                                let _e530 = local_228;
                                let _e535 = tiles.member[(_e530 >> bitcast<u32>(2u))];
                                local_229 = _e535;
                                let _e536 = local_229;
                                local_230 = select(0u, 1u, (_e536 != 0u));
                                let _e539 = local_230;
                                if (_e539 == 0u) {
                                } else {
                                    local_194 = 1000000000f;
                                }
                            }
                            let _e541 = local_209;
                            local_231 = select(0u, 1u, (bitcast<i32>(_e541) >= bitcast<i32>(0u)));
                            let _e546 = local_231;
                            if (_e546 == 0u) {
                            } else {
                                let _e548 = local_209;
                                local_232 = _e548;
                                let _e549 = local_232;
                                local_233 = _e549;
                                let _e550 = local_233;
                                local_234 = (_e550 * 4u);
                                let _e552 = local_93;
                                let _e553 = local_234;
                                local_235 = (_e552 + _e553);
                                let _e555 = local_235;
                                let _e560 = tiles.member[(_e555 >> bitcast<u32>(2u))];
                                local_236 = _e560;
                                let _e561 = local_236;
                                local_237 = select(0u, 1u, (_e561 != 0u));
                                let _e564 = local_237;
                                if (_e564 == 0u) {
                                } else {
                                    local_197 = 1000000000f;
                                }
                            }
                            local_238 = 0f;
                            local_239 = 0f;
                            local_240 = 1000000000f;
                            let _e566 = local_189;
                            let _e567 = local_240;
                            local_241 = select(0u, 1u, (_e566 < _e567));
                            let _e570 = local_241;
                            if (_e570 == 0u) {
                            } else {
                                let _e572 = local_189;
                                local_240 = _e572;
                                let _e573 = local_189;
                                let _e574 = local_112;
                                local_242 = (_e573 + _e574);
                                let _e576 = local_242;
                                local_243 = -(_e576);
                                let _e578 = local_243;
                                local_238 = _e578;
                                local_239 = 0f;
                            }
                            let _e579 = local_192;
                            let _e580 = local_240;
                            local_244 = select(0u, 1u, (_e579 < _e580));
                            let _e583 = local_244;
                            if (_e583 == 0u) {
                            } else {
                                let _e585 = local_192;
                                local_240 = _e585;
                                let _e586 = local_192;
                                let _e587 = local_112;
                                local_245 = (_e586 + _e587);
                                let _e589 = local_245;
                                local_238 = _e589;
                                local_239 = 0f;
                            }
                            let _e590 = local_194;
                            let _e591 = local_240;
                            local_246 = select(0u, 1u, (_e590 < _e591));
                            let _e594 = local_246;
                            if (_e594 == 0u) {
                            } else {
                                let _e596 = local_194;
                                local_240 = _e596;
                                local_238 = 0f;
                                let _e597 = local_194;
                                let _e598 = local_112;
                                local_247 = (_e597 + _e598);
                                let _e600 = local_247;
                                local_248 = -(_e600);
                                let _e602 = local_248;
                                local_239 = _e602;
                            }
                            let _e603 = local_197;
                            let _e604 = local_240;
                            local_249 = select(0u, 1u, (_e603 < _e604));
                            let _e607 = local_249;
                            if (_e607 == 0u) {
                            } else {
                                let _e609 = local_197;
                                local_240 = _e609;
                                local_238 = 0f;
                                let _e610 = local_197;
                                let _e611 = local_112;
                                local_250 = (_e610 + _e611);
                                let _e613 = local_250;
                                local_239 = _e613;
                            }
                            let _e614 = local_117;
                            let _e615 = local_238;
                            local_251 = (_e614 + _e615);
                            let _e617 = local_251;
                            local_117 = _e617;
                            let _e618 = local_123;
                            let _e619 = local_239;
                            local_252 = (_e618 + _e619);
                            let _e621 = local_252;
                            local_123 = _e621;
                        } else {
                            let _e622 = local_112;
                            let _e623 = local_112;
                            local_177 = (_e622 * _e623);
                            let _e625 = local_175;
                            let _e626 = local_177;
                            local_178 = select(0u, 1u, (_e625 < _e626));
                            let _e629 = local_178;
                            if (_e629 == 0u) {
                            } else {
                                let _e631 = local_175;
                                local_179 = sqrt(_e631);
                                let _e633 = local_179;
                                local_180 = _e633;
                                let _e634 = local_112;
                                let _e635 = local_180;
                                local_181 = (_e634 - _e635);
                                let _e637 = local_181;
                                let _e638 = local_180;
                                local_182 = (_e637 / _e638);
                                let _e640 = local_182;
                                local_183 = _e640;
                                let _e641 = local_169;
                                let _e642 = local_183;
                                local_184 = (_e641 * _e642);
                                let _e644 = local_117;
                                let _e645 = local_184;
                                local_185 = (_e644 + _e645);
                                let _e647 = local_185;
                                local_117 = _e647;
                                let _e648 = local_171;
                                let _e649 = local_183;
                                local_186 = (_e648 * _e649);
                                let _e651 = local_123;
                                let _e652 = local_186;
                                local_187 = (_e651 + _e652);
                                let _e654 = local_187;
                                local_123 = _e654;
                            }
                        }
                    }
                    let _e655 = local_144;
                    local_253 = _e655;
                    let _e656 = local_144;
                    local_254 = (_e656 + 1u);
                    let _e658 = local_254;
                    local_144 = _e658;
                    continue;
                }
                let _e659 = local_141;
                local_255 = _e659;
                let _e660 = local_141;
                local_256 = (_e660 + 1u);
                let _e662 = local_256;
                local_141 = _e662;
                continue;
            }
        }
        let _e663 = local_102;
        local_257 = _e663;
        let _e664 = local_257;
        local_258 = (_e664 * 4u);
        let _e666 = local_91;
        let _e667 = local_258;
        local_259 = (_e666 + _e667);
        let _e669 = local_259;
        let _e674 = local_117;
        positions_1.member[(_e669 >> bitcast<u32>(2u))] = _e674;
        let _e675 = local_102;
        local_260 = (_e675 + 1u);
        let _e677 = local_260;
        local_261 = _e677;
        let _e678 = local_261;
        local_262 = (_e678 * 4u);
        let _e680 = local_91;
        let _e681 = local_262;
        local_263 = (_e680 + _e681);
        let _e683 = local_263;
        let _e688 = local_123;
        positions_1.member[(_e683 >> bitcast<u32>(2u))] = _e688;
        return;
    } else {
        return;
    }
}

@compute @workgroup_size(64, 1, 1) 
fn integrate_world(@builtin(global_invocation_id) gl_GlobalInvocationId: vec3<u32>) {
    gl_GlobalInvocationId_2 = gl_GlobalInvocationId;
    integrate_world_1();
}

@compute @workgroup_size(64, 1, 1) 
fn tile_collide(@builtin(global_invocation_id) gl_GlobalInvocationId_1: vec3<u32>) {
    gl_GlobalInvocationId_2 = gl_GlobalInvocationId_1;
    tile_collide_1();
}
