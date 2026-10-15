struct positions_buffer {
    member: array<f32>,
}

struct previous_positions_buffer {
    member: array<f32>,
}

struct radius_buffer {
    member: array<f32>,
}

struct verlet_integration_push {
    delta_time: f32,
    world_width: f32,
    world_height: f32,
    is_mouse_pressed: u32,
    mouse_x: f32,
    mouse_y: f32,
    num_particles: u32,
}

@group(0) @binding(0) 
var<storage, read_write> positions: positions_buffer;
@group(0) @binding(1) 
var<storage, read_write> previous_positions: previous_positions_buffer;
@group(0) @binding(2) 
var<storage, read_write> radius: radius_buffer;
@group(0) @binding(30) 
var<uniform> verlet_integration_args: verlet_integration_push;
var<private> gl_GlobalInvocationId_1: vec3<u32>;

fn verlet_integration_1() {
    var local: u32;
    var local_1: u32;
    var local_2: u32;
    var local_3: f32;
    var local_4: f32;
    var local_5: f32;
    var local_6: u32;
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
    var local_32: u32;
    var local_33: u32;
    var local_34: u32;
    var local_35: u32;
    var local_36: f32;
    var local_37: f32;
    var local_38: f32;
    var local_39: f32;
    var local_40: f32;
    var local_41: f32;
    var local_42: f32;
    var local_43: f32;
    var local_44: u32;
    var local_45: f32;
    var local_46: f32;
    var local_47: f32;
    var local_48: f32;
    var local_49: f32;
    var local_50: f32;
    var local_51: f32;
    var local_52: f32;
    var local_53: f32;
    var local_54: f32;
    var local_55: f32;
    var local_56: f32;
    var local_57: f32;
    var local_58: f32;
    var local_59: f32;
    var local_60: f32;
    var local_61: f32;
    var local_62: f32;
    var local_63: f32;
    var local_64: f32;
    var local_65: f32;
    var local_66: f32;
    var local_67: f32;
    var local_68: f32;
    var local_69: f32;
    var local_70: f32;
    var local_71: f32;
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
    var local_83: f32;
    var local_84: f32;
    var local_85: f32;
    var local_86: f32;
    var local_87: f32;
    var local_88: f32;
    var local_89: f32;
    var local_90: f32;
    var local_91: u32;
    var local_92: u32;
    var local_93: u32;
    var local_94: u32;
    var local_95: u32;
    var local_96: u32;
    var local_97: u32;

    local = 0u;
    local_1 = 0u;
    local_2 = 0u;
    let _e113 = verlet_integration_args.delta_time;
    local_3 = _e113;
    let _e115 = verlet_integration_args.world_width;
    local_4 = _e115;
    let _e117 = verlet_integration_args.world_height;
    local_5 = _e117;
    let _e119 = verlet_integration_args.is_mouse_pressed;
    local_6 = _e119;
    let _e121 = verlet_integration_args.mouse_x;
    local_7 = _e121;
    let _e123 = verlet_integration_args.mouse_y;
    local_8 = _e123;
    let _e125 = verlet_integration_args.num_particles;
    local_9 = _e125;
    let _e127 = gl_GlobalInvocationId_1[0u];
    local_10 = _e127;
    let _e128 = local_10;
    local_11 = _e128;
    let _e129 = local_11;
    let _e130 = local_9;
    local_12 = select(0u, 1u, (_e129 >= _e130));
    let _e133 = local_12;
    if (_e133 == 0u) {
    } else {
        return;
    }
    let _e135 = local_11;
    local_13 = (_e135 * 2u);
    let _e137 = local_13;
    local_14 = _e137;
    let _e138 = local_14;
    local_15 = _e138;
    let _e139 = local_15;
    local_16 = _e139;
    let _e140 = local_16;
    local_17 = (_e140 * 4u);
    let _e142 = local;
    let _e143 = local_17;
    local_18 = (_e142 + _e143);
    let _e145 = local_18;
    let _e150 = positions.member[(_e145 >> bitcast<u32>(2u))];
    local_19 = _e150;
    let _e151 = local_19;
    local_20 = _e151;
    let _e152 = local_15;
    local_21 = (_e152 + 1u);
    let _e154 = local_21;
    local_22 = _e154;
    let _e155 = local_22;
    local_23 = (_e155 * 4u);
    let _e157 = local;
    let _e158 = local_23;
    local_24 = (_e157 + _e158);
    let _e160 = local_24;
    let _e165 = positions.member[(_e160 >> bitcast<u32>(2u))];
    local_25 = _e165;
    let _e166 = local_25;
    local_26 = _e166;
    let _e167 = local_15;
    local_27 = _e167;
    let _e168 = local_27;
    local_28 = (_e168 * 4u);
    let _e170 = local_1;
    let _e171 = local_28;
    local_29 = (_e170 + _e171);
    let _e173 = local_29;
    let _e178 = previous_positions.member[(_e173 >> bitcast<u32>(2u))];
    local_30 = _e178;
    let _e179 = local_30;
    local_31 = _e179;
    let _e180 = local_15;
    local_32 = (_e180 + 1u);
    let _e182 = local_32;
    local_33 = _e182;
    let _e183 = local_33;
    local_34 = (_e183 * 4u);
    let _e185 = local_1;
    let _e186 = local_34;
    local_35 = (_e185 + _e186);
    let _e188 = local_35;
    let _e193 = previous_positions.member[(_e188 >> bitcast<u32>(2u))];
    local_36 = _e193;
    let _e194 = local_36;
    local_37 = _e194;
    let _e195 = local_20;
    let _e196 = local_31;
    local_38 = (_e195 - _e196);
    let _e198 = local_38;
    local_39 = _e198;
    let _e199 = local_26;
    let _e200 = local_37;
    local_40 = (_e199 - _e200);
    let _e202 = local_40;
    local_41 = _e202;
    local_42 = 0f;
    local_43 = 0f;
    let _e203 = local_6;
    local_44 = select(0u, 1u, (_e203 == 1u));
    let _e206 = local_44;
    if (_e206 == 0u) {
    } else {
        let _e208 = local_7;
        let _e209 = local_20;
        local_45 = (_e208 - _e209);
        let _e211 = local_45;
        local_46 = _e211;
        let _e212 = local_8;
        let _e213 = local_26;
        local_47 = (_e212 - _e213);
        let _e215 = local_47;
        local_48 = _e215;
        let _e216 = local_46;
        let _e217 = local_46;
        local_49 = (_e216 * _e217);
        let _e219 = local_48;
        let _e220 = local_48;
        local_50 = (_e219 * _e220);
        let _e222 = local_49;
        let _e223 = local_50;
        local_51 = (_e222 + _e223);
        let _e225 = local_51;
        local_52 = sqrt(_e225);
        let _e227 = local_52;
        local_53 = _e227;
        let _e228 = local_46;
        let _e229 = local_53;
        local_54 = (_e228 / _e229);
        local_55 = 150f;
        let _e231 = local_54;
        let _e232 = local_55;
        local_56 = (_e231 * _e232);
        let _e234 = local_42;
        let _e235 = local_56;
        local_57 = (_e234 + _e235);
        let _e237 = local_57;
        local_42 = _e237;
        let _e238 = local_48;
        let _e239 = local_53;
        local_58 = (_e238 / _e239);
        local_59 = 150f;
        let _e241 = local_58;
        let _e242 = local_59;
        local_60 = (_e241 * _e242);
        let _e244 = local_43;
        let _e245 = local_60;
        local_61 = (_e244 + _e245);
        let _e247 = local_61;
        local_43 = _e247;
    }
    let _e248 = local_3;
    let _e249 = local_3;
    local_62 = (_e248 * _e249);
    let _e251 = local_62;
    local_63 = _e251;
    let _e252 = local_20;
    let _e253 = local_39;
    local_64 = (_e252 + _e253);
    let _e255 = local_42;
    let _e256 = local_63;
    local_65 = (_e255 * _e256);
    let _e258 = local_64;
    let _e259 = local_65;
    local_66 = (_e258 + _e259);
    let _e261 = local_66;
    local_67 = _e261;
    let _e262 = local_26;
    let _e263 = local_41;
    local_68 = (_e262 + _e263);
    let _e265 = local_43;
    let _e266 = local_63;
    local_69 = (_e265 * _e266);
    let _e268 = local_68;
    let _e269 = local_69;
    local_70 = (_e268 + _e269);
    let _e271 = local_70;
    local_71 = _e271;
    let _e272 = local_15;
    local_72 = _e272;
    let _e273 = local_72;
    local_73 = (_e273 * 4u);
    let _e275 = local_1;
    let _e276 = local_73;
    local_74 = (_e275 + _e276);
    let _e278 = local_74;
    let _e283 = local_20;
    previous_positions.member[(_e278 >> bitcast<u32>(2u))] = _e283;
    let _e284 = local_15;
    local_75 = (_e284 + 1u);
    let _e286 = local_75;
    local_76 = _e286;
    let _e287 = local_76;
    local_77 = (_e287 * 4u);
    let _e289 = local_1;
    let _e290 = local_77;
    local_78 = (_e289 + _e290);
    let _e292 = local_78;
    let _e297 = local_26;
    previous_positions.member[(_e292 >> bitcast<u32>(2u))] = _e297;
    let _e298 = local_11;
    local_79 = _e298;
    let _e299 = local_79;
    local_80 = _e299;
    let _e300 = local_80;
    local_81 = (_e300 * 4u);
    let _e302 = local_2;
    let _e303 = local_81;
    local_82 = (_e302 + _e303);
    let _e305 = local_82;
    let _e310 = radius.member[(_e305 >> bitcast<u32>(2u))];
    local_83 = _e310;
    let _e311 = local_83;
    local_84 = _e311;
    let _e312 = local_67;
    let _e313 = local_84;
    local_85 = max(_e312, _e313);
    let _e315 = local_4;
    let _e316 = local_84;
    local_86 = (_e315 - _e316);
    let _e318 = local_85;
    let _e319 = local_86;
    local_87 = min(_e318, _e319);
    let _e321 = local_87;
    local_67 = _e321;
    let _e322 = local_71;
    let _e323 = local_84;
    local_88 = max(_e322, _e323);
    let _e325 = local_5;
    let _e326 = local_84;
    local_89 = (_e325 - _e326);
    let _e328 = local_88;
    let _e329 = local_89;
    local_90 = min(_e328, _e329);
    let _e331 = local_90;
    local_71 = _e331;
    let _e332 = local_15;
    local_91 = _e332;
    let _e333 = local_91;
    local_92 = (_e333 * 4u);
    let _e335 = local;
    let _e336 = local_92;
    local_93 = (_e335 + _e336);
    let _e338 = local_93;
    let _e343 = local_67;
    positions.member[(_e338 >> bitcast<u32>(2u))] = _e343;
    let _e344 = local_15;
    local_94 = (_e344 + 1u);
    let _e346 = local_94;
    local_95 = _e346;
    let _e347 = local_95;
    local_96 = (_e347 * 4u);
    let _e349 = local;
    let _e350 = local_96;
    local_97 = (_e349 + _e350);
    let _e352 = local_97;
    let _e357 = local_71;
    positions.member[(_e352 >> bitcast<u32>(2u))] = _e357;
    return;
}

@compute @workgroup_size(64, 1, 1) 
fn verlet_integration(@builtin(global_invocation_id) gl_GlobalInvocationId: vec3<u32>) {
    gl_GlobalInvocationId_1 = gl_GlobalInvocationId;
    verlet_integration_1();
}
