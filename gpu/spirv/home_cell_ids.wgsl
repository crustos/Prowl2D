struct positions_buffer {
    member: array<f32>,
}

struct home_cell_ids_buffer {
    member: array<u32>,
}

struct particle_ids_buffer {
    member: array<u32>,
}

struct create_home_cell_ids_push {
    num_particles: u32,
    cell_size: f32,
}

@group(0) @binding(0) 
var<storage, read_write> positions: positions_buffer;
@group(0) @binding(1) 
var<storage, read_write> home_cell_ids: home_cell_ids_buffer;
@group(0) @binding(2) 
var<storage, read_write> particle_ids: particle_ids_buffer;
@group(0) @binding(30) 
var<uniform> create_home_cell_ids_args: create_home_cell_ids_push;
var<private> gl_GlobalInvocationId_1: vec3<u32>;

fn split_by_bits(param: u32) -> u32 {
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
    let _e37 = local;
    local_1 = (_e37 & 65535u);
    let _e39 = local_1;
    local_2 = _e39;
    let _e40 = local_2;
    local_3 = (_e40 << bitcast<u32>((8u & 31u)));
    let _e44 = local_2;
    let _e45 = local_3;
    local_4 = (_e44 | _e45);
    let _e47 = local_4;
    local_5 = (_e47 & 16711935u);
    let _e49 = local_5;
    local_2 = _e49;
    let _e50 = local_2;
    local_6 = (_e50 << bitcast<u32>((4u & 31u)));
    let _e54 = local_2;
    let _e55 = local_6;
    local_7 = (_e54 | _e55);
    let _e57 = local_7;
    local_8 = (_e57 & 252645135u);
    let _e59 = local_8;
    local_2 = _e59;
    let _e60 = local_2;
    local_9 = (_e60 << bitcast<u32>((2u & 31u)));
    let _e64 = local_2;
    let _e65 = local_9;
    local_10 = (_e64 | _e65);
    let _e67 = local_10;
    local_11 = (_e67 & 858993459u);
    let _e69 = local_11;
    local_2 = _e69;
    let _e70 = local_2;
    local_12 = (_e70 << bitcast<u32>((1u & 31u)));
    let _e74 = local_2;
    let _e75 = local_12;
    local_13 = (_e74 | _e75);
    let _e77 = local_13;
    local_14 = (_e77 & 1431655765u);
    let _e79 = local_14;
    local_2 = _e79;
    let _e80 = local_2;
    return _e80;
}

fn morton_encode(param_1: u32, param_2: u32) -> u32 {
    var local_15: u32;
    var local_16: u32;
    var local_17: u32;
    var local_18: u32;
    var local_19: u32;
    var local_20: u32;
    var local_21: u32;
    var local_22: u32;

    local_15 = param_1;
    local_16 = param_2;
    let _e31 = local_15;
    local_17 = _e31;
    let _e32 = local_17;
    let _e33 = split_by_bits(_e32);
    local_18 = _e33;
    let _e34 = local_16;
    local_19 = _e34;
    let _e35 = local_19;
    let _e36 = split_by_bits(_e35);
    local_20 = _e36;
    let _e37 = local_20;
    local_21 = (_e37 << bitcast<u32>((1u & 31u)));
    let _e41 = local_18;
    let _e42 = local_21;
    local_22 = (_e41 | _e42);
    let _e44 = local_22;
    return _e44;
}

fn create_home_cell_ids_1() {
    var local_23: u32;
    var local_24: u32;
    var local_25: u32;
    var local_26: u32;
    var local_27: f32;
    var local_28: u32;
    var local_29: u32;
    var local_30: u32;
    var local_31: u32;
    var local_32: u32;
    var local_33: u32;
    var local_34: u32;
    var local_35: u32;
    var local_36: f32;
    var local_37: f32;
    var local_38: u32;
    var local_39: u32;
    var local_40: u32;
    var local_41: u32;
    var local_42: u32;
    var local_43: u32;
    var local_44: f32;
    var local_45: f32;
    var local_46: f32;
    var local_47: f32;
    var local_48: u32;
    var local_49: u32;
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

    local_23 = 0u;
    local_24 = 0u;
    local_25 = 0u;
    let _e62 = create_home_cell_ids_args.num_particles;
    local_26 = _e62;
    let _e64 = create_home_cell_ids_args.cell_size;
    local_27 = _e64;
    let _e66 = gl_GlobalInvocationId_1[0u];
    local_28 = _e66;
    let _e67 = local_28;
    local_29 = _e67;
    let _e68 = local_29;
    let _e69 = local_26;
    local_30 = select(0u, 1u, (_e68 >= _e69));
    let _e72 = local_30;
    if (_e72 == 0u) {
        let _e74 = local_29;
        local_31 = (_e74 * 2u);
        let _e76 = local_31;
        local_32 = _e76;
        let _e77 = local_32;
        local_33 = _e77;
        let _e78 = local_33;
        local_34 = (_e78 * 4u);
        let _e80 = local_23;
        let _e81 = local_34;
        local_35 = (_e80 + _e81);
        let _e83 = local_35;
        let _e88 = positions.member[(_e83 >> bitcast<u32>(2u))];
        local_36 = _e88;
        let _e89 = local_36;
        local_37 = _e89;
        let _e90 = local_29;
        local_38 = (_e90 * 2u);
        let _e92 = local_38;
        local_39 = (_e92 + 1u);
        let _e94 = local_39;
        local_40 = _e94;
        let _e95 = local_40;
        local_41 = _e95;
        let _e96 = local_41;
        local_42 = (_e96 * 4u);
        let _e98 = local_23;
        let _e99 = local_42;
        local_43 = (_e98 + _e99);
        let _e101 = local_43;
        let _e106 = positions.member[(_e101 >> bitcast<u32>(2u))];
        local_44 = _e106;
        let _e107 = local_44;
        local_45 = _e107;
        let _e108 = local_37;
        let _e109 = local_27;
        local_46 = (_e108 / _e109);
        let _e111 = local_46;
        local_47 = floor(_e111);
        let _e113 = local_47;
        let _e115 = select(_e113, 0f, (_e113 != _e113));
        local_48 = select(u32(clamp(_e115, -2147483600f, 2147483500f)), 2147483647u, (_e115 >= 2147483600f));
        let _e120 = local_48;
        local_49 = _e120;
        let _e121 = local_45;
        let _e122 = local_27;
        local_50 = (_e121 / _e122);
        let _e124 = local_50;
        local_51 = floor(_e124);
        let _e126 = local_51;
        let _e128 = select(_e126, 0f, (_e126 != _e126));
        local_52 = select(u32(clamp(_e128, -2147483600f, 2147483500f)), 2147483647u, (_e128 >= 2147483600f));
        let _e133 = local_52;
        local_53 = _e133;
        let _e134 = local_49;
        let _e135 = local_53;
        let _e136 = morton_encode(_e134, _e135);
        local_54 = _e136;
        let _e137 = local_29;
        local_55 = _e137;
        let _e138 = local_55;
        local_56 = _e138;
        let _e139 = local_56;
        local_57 = (_e139 * 4u);
        let _e141 = local_24;
        let _e142 = local_57;
        local_58 = (_e141 + _e142);
        let _e144 = local_58;
        let _e149 = local_54;
        home_cell_ids.member[(_e144 >> bitcast<u32>(2u))] = _e149;
        let _e150 = local_29;
        local_59 = _e150;
        let _e151 = local_59;
        local_60 = _e151;
        let _e152 = local_60;
        local_61 = (_e152 * 4u);
        let _e154 = local_25;
        let _e155 = local_61;
        local_62 = (_e154 + _e155);
        let _e157 = local_62;
        let _e162 = local_29;
        particle_ids.member[(_e157 >> bitcast<u32>(2u))] = _e162;
        return;
    } else {
        return;
    }
}

@compute @workgroup_size(64, 1, 1) 
fn create_home_cell_ids(@builtin(global_invocation_id) gl_GlobalInvocationId: vec3<u32>) {
    gl_GlobalInvocationId_1 = gl_GlobalInvocationId;
    create_home_cell_ids_1();
}
