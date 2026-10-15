struct positions_read_buffer {
    member: array<f32>,
}

struct radius_read_buffer {
    member: array<f32>,
}

struct previous_positions_read_buffer {
    member: array<f32>,
}

struct particle_ids_buffer {
    member: array<u32>,
}

struct positions_write_buffer {
    member: array<f32>,
}

struct radius_write_buffer {
    member: array<f32>,
}

struct previous_positions_write_buffer {
    member: array<f32>,
}

struct rearrange_push {
    num_particles: u32,
}

@group(0) @binding(0) 
var<storage, read_write> positions_read: positions_read_buffer;
@group(0) @binding(1) 
var<storage, read_write> radius_read: radius_read_buffer;
@group(0) @binding(2) 
var<storage, read_write> previous_positions_read: previous_positions_read_buffer;
@group(0) @binding(3) 
var<storage, read_write> particle_ids: particle_ids_buffer;
@group(0) @binding(4) 
var<storage, read_write> positions_write: positions_write_buffer;
@group(0) @binding(5) 
var<storage, read_write> radius_write: radius_write_buffer;
@group(0) @binding(6) 
var<storage, read_write> previous_positions_write: previous_positions_write_buffer;
@group(0) @binding(30) 
var<uniform> rearrange_args: rearrange_push;
var<private> gl_GlobalInvocationId_1: vec3<u32>;

fn rearrange_1() {
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
    var local_26: f32;
    var local_27: u32;
    var local_28: u32;
    var local_29: u32;
    var local_30: u32;
    var local_31: u32;
    var local_32: u32;
    var local_33: u32;
    var local_34: f32;
    var local_35: u32;
    var local_36: u32;
    var local_37: u32;
    var local_38: u32;
    var local_39: u32;
    var local_40: u32;
    var local_41: u32;
    var local_42: u32;
    var local_43: f32;
    var local_44: u32;
    var local_45: u32;
    var local_46: u32;
    var local_47: u32;
    var local_48: u32;
    var local_49: u32;
    var local_50: u32;
    var local_51: f32;
    var local_52: u32;
    var local_53: u32;
    var local_54: u32;
    var local_55: u32;
    var local_56: u32;
    var local_57: u32;
    var local_58: u32;
    var local_59: f32;
    var local_60: u32;
    var local_61: u32;
    var local_62: u32;
    var local_63: u32;

    local = 0u;
    local_1 = 0u;
    local_2 = 0u;
    local_3 = 0u;
    local_4 = 0u;
    local_5 = 0u;
    local_6 = 0u;
    let _e78 = rearrange_args.num_particles;
    local_7 = _e78;
    let _e80 = gl_GlobalInvocationId_1[0u];
    local_8 = _e80;
    let _e81 = local_8;
    local_9 = _e81;
    let _e82 = local_9;
    let _e83 = local_7;
    local_10 = select(0u, 1u, (_e82 >= _e83));
    let _e86 = local_10;
    if (_e86 == 0u) {
        let _e88 = local_9;
        local_11 = _e88;
        let _e89 = local_11;
        local_12 = _e89;
        let _e90 = local_12;
        local_13 = (_e90 * 4u);
        let _e92 = local_3;
        let _e93 = local_13;
        local_14 = (_e92 + _e93);
        let _e95 = local_14;
        let _e100 = particle_ids.member[(_e95 >> bitcast<u32>(2u))];
        local_15 = _e100;
        let _e101 = local_15;
        local_16 = _e101;
        let _e102 = local_16;
        local_17 = (_e102 * 2u);
        let _e104 = local_17;
        local_18 = _e104;
        let _e105 = local_18;
        local_19 = _e105;
        let _e106 = local_9;
        local_20 = (_e106 * 2u);
        let _e108 = local_20;
        local_21 = _e108;
        let _e109 = local_21;
        local_22 = _e109;
        let _e110 = local_19;
        local_23 = _e110;
        let _e111 = local_23;
        local_24 = (_e111 * 4u);
        let _e113 = local;
        let _e114 = local_24;
        local_25 = (_e113 + _e114);
        let _e116 = local_25;
        let _e121 = positions_read.member[(_e116 >> bitcast<u32>(2u))];
        local_26 = _e121;
        let _e122 = local_22;
        local_27 = _e122;
        let _e123 = local_27;
        local_28 = (_e123 * 4u);
        let _e125 = local_4;
        let _e126 = local_28;
        local_29 = (_e125 + _e126);
        let _e128 = local_29;
        let _e133 = local_26;
        positions_write.member[(_e128 >> bitcast<u32>(2u))] = _e133;
        let _e134 = local_19;
        local_30 = (_e134 + 1u);
        let _e136 = local_30;
        local_31 = _e136;
        let _e137 = local_31;
        local_32 = (_e137 * 4u);
        let _e139 = local;
        let _e140 = local_32;
        local_33 = (_e139 + _e140);
        let _e142 = local_33;
        let _e147 = positions_read.member[(_e142 >> bitcast<u32>(2u))];
        local_34 = _e147;
        let _e148 = local_22;
        local_35 = (_e148 + 1u);
        let _e150 = local_35;
        local_36 = _e150;
        let _e151 = local_36;
        local_37 = (_e151 * 4u);
        let _e153 = local_4;
        let _e154 = local_37;
        local_38 = (_e153 + _e154);
        let _e156 = local_38;
        let _e161 = local_34;
        positions_write.member[(_e156 >> bitcast<u32>(2u))] = _e161;
        let _e162 = local_16;
        local_39 = _e162;
        let _e163 = local_39;
        local_40 = _e163;
        let _e164 = local_40;
        local_41 = (_e164 * 4u);
        let _e166 = local_1;
        let _e167 = local_41;
        local_42 = (_e166 + _e167);
        let _e169 = local_42;
        let _e174 = radius_read.member[(_e169 >> bitcast<u32>(2u))];
        local_43 = _e174;
        let _e175 = local_9;
        local_44 = _e175;
        let _e176 = local_44;
        local_45 = _e176;
        let _e177 = local_45;
        local_46 = (_e177 * 4u);
        let _e179 = local_5;
        let _e180 = local_46;
        local_47 = (_e179 + _e180);
        let _e182 = local_47;
        let _e187 = local_43;
        radius_write.member[(_e182 >> bitcast<u32>(2u))] = _e187;
        let _e188 = local_19;
        local_48 = _e188;
        let _e189 = local_48;
        local_49 = (_e189 * 4u);
        let _e191 = local_2;
        let _e192 = local_49;
        local_50 = (_e191 + _e192);
        let _e194 = local_50;
        let _e199 = previous_positions_read.member[(_e194 >> bitcast<u32>(2u))];
        local_51 = _e199;
        let _e200 = local_22;
        local_52 = _e200;
        let _e201 = local_52;
        local_53 = (_e201 * 4u);
        let _e203 = local_6;
        let _e204 = local_53;
        local_54 = (_e203 + _e204);
        let _e206 = local_54;
        let _e211 = local_51;
        previous_positions_write.member[(_e206 >> bitcast<u32>(2u))] = _e211;
        let _e212 = local_19;
        local_55 = (_e212 + 1u);
        let _e214 = local_55;
        local_56 = _e214;
        let _e215 = local_56;
        local_57 = (_e215 * 4u);
        let _e217 = local_2;
        let _e218 = local_57;
        local_58 = (_e217 + _e218);
        let _e220 = local_58;
        let _e225 = previous_positions_read.member[(_e220 >> bitcast<u32>(2u))];
        local_59 = _e225;
        let _e226 = local_22;
        local_60 = (_e226 + 1u);
        let _e228 = local_60;
        local_61 = _e228;
        let _e229 = local_61;
        local_62 = (_e229 * 4u);
        let _e231 = local_6;
        let _e232 = local_62;
        local_63 = (_e231 + _e232);
        let _e234 = local_63;
        let _e239 = local_59;
        previous_positions_write.member[(_e234 >> bitcast<u32>(2u))] = _e239;
        return;
    } else {
        return;
    }
}

@compute @workgroup_size(64, 1, 1) 
fn rearrange(@builtin(global_invocation_id) gl_GlobalInvocationId: vec3<u32>) {
    gl_GlobalInvocationId_1 = gl_GlobalInvocationId;
    rearrange_1();
}
